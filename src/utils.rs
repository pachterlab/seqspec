use crate::models::assay::Assay;
use crate::models::read::Read;
use crate::models::region::{Region, RegionCoordinate};

use serde_yaml;
use reqwest;
use flate2::read::GzDecoder;


pub fn complement_base(c: char) -> char {
    match c {
        'A' => 'T', 'T' => 'A', 'G' => 'C', 'C' => 'G',
        'R' => 'Y', 'Y' => 'R', 'S' => 'S', 'W' => 'W',
        'K' => 'M', 'M' => 'K', 'B' => 'V', 'D' => 'H',
        'V' => 'B', 'H' => 'D', 'N' => 'N', 'X' => 'X',
        _ => 'N',
    }
}

pub fn complement_seq(s: &str) -> String {
    s.chars().map(|c| complement_base(c.to_ascii_uppercase())).collect()
}

// pub fn to_pydict<T: serde::Serialize>(py: Python<'_>, v: &T) -> Result<PyObject, serde_json::Error> {
//     let obj = pythonize::pythonize(py, v)?;
//     Ok(obj.into())
// }


pub fn load_spec(spec: &std::path::PathBuf) -> Assay {
    // read in the spec file
    let f: std::fs::File = std::fs::File::open(spec).expect("Could not open file.");

    // convert it to an assay object
    let spec: Assay = serde_yaml::from_reader(f).expect("Could not read values.");

    return spec;
}

/// Read a local text file into Vec<String>, handling optional .gz
pub fn read_local_list(path: &std::path::Path) -> Result<Vec<String>, String> {
    let p = if path.exists() { path.to_path_buf() } else {
        let gz = std::path::PathBuf::from(format!("{}.gz", path.display()));
        gz
    };
    if !p.exists() { return Err(format!("path not found: {}", path.display())); }
    if p.extension().map(|e| e == "gz").unwrap_or(false) {
        let f = std::fs::File::open(&p).map_err(|e| e.to_string())?;
        let mut dec = GzDecoder::new(f);
        let mut s = String::new();
        use std::io::Read; dec.read_to_string(&mut s).map_err(|e| e.to_string())?;
        Ok(s.lines().map(|l| l.trim().to_string()).filter(|l| !l.is_empty()).collect())
    } else {
        let s = std::fs::read_to_string(&p).map_err(|e| e.to_string())?;
        Ok(s.lines().map(|l| l.trim().to_string()).filter(|l| !l.is_empty()).collect())
    }
}

/// Fetch a remote text file (http/https/ftp) and return lines
pub fn read_remote_list(url: &str) -> Result<Vec<String>, String> {
    let resp = reqwest::blocking::get(url).map_err(|e| e.to_string())?;
    if !resp.status().is_success() { return Err(format!("bad status: {}", resp.status())); }
    let bytes = resp.bytes().map_err(|e| e.to_string())?;
    let data: Vec<u8> = bytes.to_vec();
    // Try gunzip if looks like gz
    let text = if url.ends_with(".gz") {
        let mut dec = GzDecoder::new(&data[..]);
        let mut s = String::new();
        use std::io::Read; dec.read_to_string(&mut s).map_err(|e| e.to_string())?;
        s
    } else {
        String::from_utf8(data).map_err(|e| e.to_string())?
    };
    Ok(text.lines().map(|l| l.trim().to_string()).filter(|l| !l.is_empty()).collect())
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
            format!(
                "primer_id '{}' not found in regions {:?}",
                primer_id, ids
            )
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
pub fn itx_read(region_coordinates: Vec<RegionCoordinate>, read_start: i64, read_stop: i64) -> Vec<RegionCoordinate> {
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