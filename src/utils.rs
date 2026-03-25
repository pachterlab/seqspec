use crate::auth::RemoteAccess;
use crate::compat::AssayCompat;
use crate::models::assay::Assay;
use crate::models::onlist::Onlist;
use crate::models::read::Read;
use crate::models::region::{Region, RegionCoordinate};

use flate2::read::GzDecoder;
use serde_yaml;
use std::io::Read as IoRead;

pub fn complement_base(c: char) -> char {
    match c {
        'A' => 'T',
        'T' => 'A',
        'G' => 'C',
        'C' => 'G',
        'R' => 'Y',
        'Y' => 'R',
        'S' => 'S',
        'W' => 'W',
        'K' => 'M',
        'M' => 'K',
        'B' => 'V',
        'D' => 'H',
        'V' => 'B',
        'H' => 'D',
        'N' => 'N',
        'X' => 'X',
        _ => 'N',
    }
}

pub fn complement_seq(s: &str) -> String {
    s.chars()
        .map(|c| complement_base(c.to_ascii_uppercase()))
        .collect()
}

// pub fn to_pydict<T: serde::Serialize>(py: Python<'_>, v: &T) -> Result<PyObject, serde_json::Error> {
//     let obj = pythonize::pythonize(py, v)?;
//     Ok(obj.into())
// }

pub fn load_spec(spec: &std::path::PathBuf) -> Assay {
    let mut f: std::fs::File = std::fs::File::open(spec).expect("Could not open file.");
    let mut magic = [0_u8; 2];
    f.read_exact(&mut magic)
        .expect("Could not read file header.");
    drop(f);

    let reader: Box<dyn IoRead> = if magic == [0x1f, 0x8b] {
        let gz = GzDecoder::new(std::fs::File::open(spec).expect("Could not open file."));
        Box::new(gz)
    } else {
        Box::new(std::fs::File::open(spec).expect("Could not open file."))
    };

    let spec: AssayCompat = serde_yaml::from_reader(reader).expect("Could not read values.");

    spec.into_assay()
}

pub fn local_resource_url<'a>(
    url: &'a str,
    filename: &str,
    resource: &str,
) -> Result<&'a str, String> {
    if url.is_empty() {
        Err(format!("local {} '{}' has empty url", resource, filename))
    } else {
        Ok(url)
    }
}

pub fn local_onlist_locator(onlist: &Onlist) -> Result<&str, String> {
    local_resource_url(&onlist.url, &onlist.filename, "onlist")
}

/// Read a local text file into Vec<String>, handling optional .gz
pub fn read_local_list(path: &std::path::Path) -> Result<Vec<String>, String> {
    let p = if path.exists() {
        path.to_path_buf()
    } else {
        let gz = std::path::PathBuf::from(format!("{}.gz", path.display()));
        gz
    };
    if !p.exists() {
        return Err(format!("path not found: {}", path.display()));
    }
    if p.extension().map(|e| e == "gz").unwrap_or(false) {
        let f = std::fs::File::open(&p).map_err(|e| e.to_string())?;
        let mut dec = GzDecoder::new(f);
        let mut s = String::new();
        use std::io::Read;
        dec.read_to_string(&mut s).map_err(|e| e.to_string())?;
        Ok(s.lines()
            .map(|l| l.trim().to_string())
            .filter(|l| !l.is_empty())
            .collect())
    } else {
        let s = std::fs::read_to_string(&p).map_err(|e| e.to_string())?;
        Ok(s.lines()
            .map(|l| l.trim().to_string())
            .filter(|l| !l.is_empty())
            .collect())
    }
}

/// Fetch a remote text file (http/https/ftp) and return lines
pub fn read_remote_list(url: &str, remote_access: &RemoteAccess) -> Result<Vec<String>, String> {
    let text = remote_access
        .with_reader(url, |mut reader| {
            let mut data = Vec::new();
            reader.read_to_end(&mut data)?;
            let text = if url.ends_with(".gz") {
                let mut dec = GzDecoder::new(&data[..]);
                let mut s = String::new();
                dec.read_to_string(&mut s)?;
                s
            } else {
                String::from_utf8(data)?
            };
            Ok(text)
        })
        .map_err(|e| e.to_string())?;
    Ok(text
        .lines()
        .map(|l| l.trim().to_string())
        .filter(|l| !l.is_empty())
        .collect())
}

/// Map a read_id to the ordered list of regions on that read's strand.
///
/// Behavior mirrors Python utils.map_read_id_to_regions:
/// - Find the `Read` by `read_id` and its `primer_id`.
/// - From the library spec for `modality`, collect an ordered list where the
///   primer region is present (but not its children).
/// - If strand is "neg", return all regions before the primer in reverse order.
///   Else, return all regions after the primer in forward order.
pub fn map_read_id_to_regions(
    spec: &Assay,
    modality: &str,
    read_id: &str,
) -> Result<(Read, Vec<Region>), String> {
    // get the read object and primer id
    let read = spec
        .get_read(read_id)
        .ok_or_else(|| format!("read_id '{}' not found", read_id))?;
    let primer_id = read.primer_id.clone();

    // get all atomic elements from library
    let libspec = spec
        .get_libspec(modality)
        .ok_or_else(|| format!("modality '{}' not found in library_spec", modality))?;

    // get the (ordered) leaves ensuring region with primer_id is included (but not its children)
    let leaves = libspec.get_leaves_with_region_id(&primer_id);

    // get the index of the primer in the list of leaves
    let primer_idx = leaves
        .iter()
        .position(|leaf| leaf.region_id == primer_id)
        .ok_or_else(|| {
            let ids: Vec<String> = leaves.iter().map(|l| l.region_id.clone()).collect();
            format!("primer_id '{}' not found in regions {:?}", primer_id, ids)
        })?;

    // If we are on the opposite strand, we go in the opposite way
    let rgns: Vec<Region> = if read.strand == "neg" {
        let mut v = leaves[..primer_idx].to_vec();
        v.reverse();
        v
    } else {
        leaves[primer_idx + 1..].to_vec()
    };

    Ok((read, rgns))
}

/// Given an ordered list of Regions, produce contiguous RegionCoordinates
/// with half-open ranges [start, stop), where each region spans its max_len.
pub fn project_regions_to_coordinates(regions: Vec<Region>) -> Vec<RegionCoordinate> {
    let mut rcs: Vec<RegionCoordinate> = Vec::new();
    let mut prev: i64 = 0;
    for region in regions.into_iter() {
        let nxt = prev + region.max_len;
        rcs.push(RegionCoordinate::new(region, prev, nxt));
        prev = nxt;
    }
    rcs
}

/// Intersect a list of RegionCoordinates with a read window [read_start, read_stop).
/// Returns only overlapping coordinates, trimmed to the window.
pub fn itx_read(
    region_coordinates: Vec<RegionCoordinate>,
    read_start: i64,
    read_stop: i64,
) -> Vec<RegionCoordinate> {
    let mut new_rcs: Vec<RegionCoordinate> = Vec::new();
    for rc in region_coordinates.into_iter() {
        if read_start >= rc.stop || read_stop <= rc.start {
            continue;
        }

        let mut rc_copy = rc.clone();
        if read_start >= rc_copy.start {
            rc_copy.start = read_start;
        }
        if read_stop < rc_copy.stop {
            rc_copy.stop = read_stop;
        }
        new_rcs.push(rc_copy);
    }
    new_rcs
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::region::Region;
    use std::path::PathBuf;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_load_spec_reads_gzipped_yaml() {
        let spec = load_spec(&PathBuf::from("tests/fixtures/spec.yaml.gz"));
        assert_eq!(spec.assay_id, "DOGMAseq-DIG");
        assert_eq!(spec.seqspec_version, Some("0.4.0".to_string()));
    }

    fn leaf(id: &str, len: i64) -> Region {
        Region::new(
            id.into(),
            "barcode".into(),
            id.into(),
            "fixed".into(),
            "A".repeat(len as usize),
            len,
            len,
            None,
            vec![],
        )
    }

    // ---- complement ----

    #[test]
    fn test_complement_base_standard() {
        assert_eq!(complement_base('A'), 'T');
        assert_eq!(complement_base('T'), 'A');
        assert_eq!(complement_base('C'), 'G');
        assert_eq!(complement_base('G'), 'C');
    }

    #[test]
    fn test_complement_base_iupac() {
        assert_eq!(complement_base('R'), 'Y');
        assert_eq!(complement_base('Y'), 'R');
        assert_eq!(complement_base('S'), 'S');
        assert_eq!(complement_base('W'), 'W');
        assert_eq!(complement_base('K'), 'M');
        assert_eq!(complement_base('M'), 'K');
        assert_eq!(complement_base('B'), 'V');
        assert_eq!(complement_base('V'), 'B');
        assert_eq!(complement_base('D'), 'H');
        assert_eq!(complement_base('H'), 'D');
        assert_eq!(complement_base('N'), 'N');
        assert_eq!(complement_base('X'), 'X');
    }

    #[test]
    fn test_complement_base_unknown() {
        assert_eq!(complement_base('Z'), 'N');
        assert_eq!(complement_base('?'), 'N');
    }

    #[test]
    fn test_complement_seq() {
        assert_eq!(complement_seq("ATCG"), "TAGC");
        assert_eq!(complement_seq("AAAA"), "TTTT");
        assert_eq!(complement_seq(""), "");
    }

    #[test]
    fn test_complement_seq_lowercase() {
        assert_eq!(complement_seq("atcg"), "TAGC");
        assert_eq!(complement_seq("AaTt"), "TTAA");
    }

    // ---- load_spec ----

    #[test]
    fn test_load_spec() {
        let spec = dogma_spec();
        assert_eq!(spec.assay_id, "DOGMAseq-DIG");
        assert_eq!(spec.modalities.len(), 4);
        assert_eq!(spec.sequence_spec.len(), 9); // 2 RNA + 3 ATAC + 2 Protein + 2 Tag
        assert_eq!(spec.library_spec.len(), 4);
    }

    #[test]
    fn test_load_spec_accepts_legacy_scalar_protocol_fields() {
        let spec = load_spec(&PathBuf::from(
            "tests/fixtures/legacy_0_3_scalar_protocols.yaml",
        ));

        assert_eq!(spec.seqspec_version, Some("0.3.0".to_string()));
        assert_eq!(spec.modalities, vec!["rna".to_string()]);

        let sequence_protocol = spec.sequence_protocol.expect("sequence protocol");
        assert_eq!(sequence_protocol.len(), 1);
        assert_eq!(sequence_protocol[0].protocol_id, "NovaSeq");
        assert_eq!(sequence_protocol[0].name, "NovaSeq");
        assert_eq!(sequence_protocol[0].modality, "rna");

        let library_kit = spec.library_kit.expect("library kit");
        assert_eq!(library_kit.len(), 1);
        assert_eq!(library_kit[0].kit_id, "LegacyKit");
        assert_eq!(library_kit[0].name.as_deref(), Some("LegacyKit"));
        assert_eq!(library_kit[0].modality, "rna");
    }

    #[test]
    fn test_load_spec_accepts_legacy_missing_files_and_short_onlist() {
        let spec = load_spec(&PathBuf::from(
            "tests/fixtures/legacy_0_2_missing_fields.yaml",
        ));

        assert_eq!(spec.seqspec_version, Some("0.2.0".to_string()));
        assert_eq!(spec.sequence_spec.len(), 1);
        assert!(spec.sequence_spec[0].files.is_empty());

        let barcode = spec.library_spec[0]
            .get_region_by_id("barcode")
            .into_iter()
            .next()
            .expect("barcode region");
        let onlist = barcode.onlist.expect("barcode onlist");
        assert_eq!(onlist.filename, "whitelist.txt.gz");
        assert_eq!(onlist.md5, "abc123");
        assert_eq!(onlist.file_id, "");
        assert_eq!(onlist.urltype, "local");
    }

    // ---- map_read_id_to_regions ----

    #[test]
    fn test_map_read_id_to_regions_pos() {
        let spec = dogma_spec();
        let result = map_read_id_to_regions(&spec, "rna", "rna_R1");
        assert!(result.is_ok());
        let (r, regions) = result.unwrap();
        assert_eq!(r.read_id, "rna_R1");
        assert_eq!(r.strand, "pos");
        assert_eq!(regions.len(), 4);
        let region_ids: Vec<&str> = regions.iter().map(|r| r.region_id.as_str()).collect();
        assert_eq!(
            region_ids,
            vec!["rna_cell_bc", "rna_umi", "cdna", "rna_truseq_read2"]
        );
    }

    #[test]
    fn test_map_read_id_to_regions_neg() {
        let spec = dogma_spec();
        let result = map_read_id_to_regions(&spec, "rna", "rna_R2");
        assert!(result.is_ok());
        let (r, regions) = result.unwrap();
        assert_eq!(r.read_id, "rna_R2");
        assert_eq!(r.strand, "neg");
        assert_eq!(regions.len(), 4);
        // Negative strand reverses the region order
        let region_ids: Vec<&str> = regions.iter().map(|r| r.region_id.as_str()).collect();
        assert_eq!(
            region_ids,
            vec!["cdna", "rna_umi", "rna_cell_bc", "rna_truseq_read1"]
        );
    }

    #[test]
    fn test_map_read_id_to_regions_invalid_read() {
        let spec = dogma_spec();
        let result = map_read_id_to_regions(&spec, "rna", "nonexistent_read");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("not found"));
    }

    #[test]
    fn test_map_read_id_to_regions_invalid_modality() {
        let spec = dogma_spec();
        let result = map_read_id_to_regions(&spec, "nonexistent", "rna_R1");
        assert!(result.is_err());
    }

    // ---- project_regions_to_coordinates ----

    #[test]
    fn test_project_regions_to_coordinates() {
        let regions = vec![leaf("a", 10), leaf("b", 20), leaf("c", 5)];
        let coords = project_regions_to_coordinates(regions);
        assert_eq!(coords.len(), 3);
        assert_eq!(coords[0].start, 0);
        assert_eq!(coords[0].stop, 10);
        assert_eq!(coords[1].start, 10);
        assert_eq!(coords[1].stop, 30);
        assert_eq!(coords[2].start, 30);
        assert_eq!(coords[2].stop, 35);
    }

    // ---- itx_read ----

    #[test]
    fn test_itx_read() {
        let regions = vec![leaf("a", 10), leaf("b", 20), leaf("c", 5)];
        let coords = project_regions_to_coordinates(regions);

        // Read window [5, 25) — should trim a and b, exclude c
        let result = itx_read(coords, 5, 25);
        assert_eq!(result.len(), 2);
        assert_eq!(result[0].start, 5);
        assert_eq!(result[0].stop, 10);
        assert_eq!(result[1].start, 10);
        assert_eq!(result[1].stop, 25);
    }

    #[test]
    fn test_itx_read_no_overlap() {
        let regions = vec![leaf("a", 10)];
        let coords = project_regions_to_coordinates(regions);
        let result = itx_read(coords, 20, 30);
        assert!(result.is_empty());
    }

    #[test]
    fn test_itx_read_full_overlap() {
        let regions = vec![leaf("a", 10)];
        let coords = project_regions_to_coordinates(regions);
        let result = itx_read(coords, 0, 100);
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].start, 0);
        assert_eq!(result[0].stop, 10);
    }

    // ---- read_local_list ----

    #[test]
    fn test_read_local_list_plain() {
        let path = PathBuf::from("tests/fixtures/onlist_joined.txt");
        let result = read_local_list(&path).unwrap();
        assert_eq!(result.len(), 736320);
        assert_eq!(result[0], "AAACAGCCAAACAACA");
    }

    #[test]
    fn test_read_local_list_gz() {
        let path = PathBuf::from("tests/fixtures/RNA-737K-arc-v1.txt.gz");
        let result = read_local_list(&path).unwrap();
        assert_eq!(result.len(), 736320);
    }

    #[test]
    fn test_read_local_list_gz_fallback() {
        // Try path without .gz extension — read_local_list should find the .gz variant
        let path = PathBuf::from("tests/fixtures/RNA-737K-arc-v1.txt");
        let result = read_local_list(&path).unwrap();
        assert_eq!(result.len(), 736320);
    }

    #[test]
    fn test_read_local_list_not_found() {
        let path = PathBuf::from("tests/fixtures/nonexistent.txt");
        let result = read_local_list(&path);
        assert!(result.is_err());
    }

    #[test]
    fn test_local_onlist_locator_prefers_url_when_present() {
        let onlist = Onlist::new(
            "ol1".into(),
            "display.txt".into(),
            "txt".into(),
            0,
            "nested/whitelist.txt".into(),
            "local".into(),
            String::new(),
        );

        assert_eq!(
            local_onlist_locator(&onlist).unwrap(),
            "nested/whitelist.txt"
        );
    }

    #[test]
    fn test_local_onlist_locator_errors_when_url_is_empty() {
        let onlist = Onlist::new(
            "ol1".into(),
            "display.txt".into(),
            "txt".into(),
            0,
            String::new(),
            "local".into(),
            String::new(),
        );

        assert_eq!(
            local_onlist_locator(&onlist).unwrap_err(),
            "local onlist 'display.txt' has empty url"
        );
    }

    #[test]
    fn test_local_resource_url_errors_when_url_is_empty() {
        assert_eq!(
            local_resource_url("", "display.fastq.gz", "file").unwrap_err(),
            "local file 'display.fastq.gz' has empty url"
        );
    }
}
