use crate::models::assay::{Assay, LibKit, LibProtocol, SeqKit, SeqProtocol};
use crate::models::file::File;
use crate::models::onlist::Onlist;
use crate::models::read::Read;
use crate::models::region::Region;
use crate::utils;
use serde::Serialize;

const TEMPLATE_HTML: &str = include_str!("../seqspec/report_assets/template.html");
const STYLE_CSS: &str = include_str!("../seqspec/report_assets/style.css");
const APP_JS: &str = include_str!("../seqspec/report_assets/app.js");

#[derive(Debug, Serialize)]
pub struct SeqspecViewData {
    assay_id: String,
    assay_name: String,
    seqspec_version: Option<String>,
    doi: String,
    date: String,
    description: String,
    lib_struct: String,
    modalities: Vec<ModalityView>,
}

#[derive(Debug, Serialize)]
pub struct ModalityView {
    modality: String,
    library_region_id: String,
    total_bp: i64,
    sequence_protocols: Vec<MetadataRow>,
    sequence_kits: Vec<MetadataRow>,
    library_protocols: Vec<MetadataRow>,
    library_kits: Vec<MetadataRow>,
    region_nodes: Vec<RegionView>,
    regions: Vec<RegionView>,
    reads: Vec<ReadView>,
}

#[derive(Debug, Serialize)]
pub struct MetadataRow {
    #[serde(skip_serializing_if = "Option::is_none")]
    protocol_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    kit_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    name: Option<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct RegionView {
    region_id: String,
    region_type: String,
    name: String,
    sequence_type: String,
    sequence: String,
    min_len: i64,
    max_len: i64,
    len: i64,
    bp_start: i64,
    bp_end: i64,
    depth: usize,
    parent_region_id: Option<String>,
    path_region_ids: Vec<String>,
    path_names: Vec<String>,
    is_leaf: bool,
    child_region_ids: Vec<String>,
    onlist: Option<OnlistView>,
}

#[derive(Clone, Debug, Serialize)]
pub struct OnlistView {
    file_id: String,
    filename: String,
    filetype: String,
    filesize: i64,
    url: String,
    urltype: String,
    md5: String,
}

#[derive(Debug, Serialize)]
pub struct ReadView {
    read_id: String,
    name: String,
    label: String,
    primer_id: String,
    min_len: i64,
    max_len: i64,
    strand: String,
    start: i64,
    end: i64,
    files: Vec<FileView>,
}

#[derive(Debug, Serialize)]
pub struct FileView {
    file_id: String,
    filename: String,
    filetype: String,
    filesize: i64,
    url: String,
    urltype: String,
    md5: String,
}

pub fn render_seqspec_html(spec: &Assay) -> Result<String, String> {
    let payload = build_seqspec_view_data(spec)?;
    let payload_json =
        escape_script_json(&serde_json::to_string(&payload).map_err(|e| e.to_string())?);
    let repository_json =
        serde_json::to_string(env!("CARGO_PKG_REPOSITORY")).map_err(|e| e.to_string())?;
    let version_json =
        serde_json::to_string(env!("CARGO_PKG_VERSION")).map_err(|e| e.to_string())?;

    Ok(TEMPLATE_HTML
        .replace("__STYLE__", STYLE_CSS)
        .replace("__APP__", APP_JS)
        .replace("__DATA__", &payload_json)
        .replace("__REPOSITORY__", &repository_json)
        .replace("__TOOL_VERSION__", &version_json))
}

pub fn build_seqspec_view_data(spec: &Assay) -> Result<SeqspecViewData, String> {
    let mut modalities = Vec::new();
    for modality in &spec.modalities {
        modalities.push(build_modality_view(spec, modality)?);
    }

    Ok(SeqspecViewData {
        assay_id: spec.assay_id.clone(),
        assay_name: spec.name.clone(),
        seqspec_version: spec.seqspec_version.clone(),
        doi: spec.doi.clone(),
        date: spec.date.clone(),
        description: spec.description.clone(),
        lib_struct: spec.lib_struct.clone(),
        modalities,
    })
}

fn build_modality_view(spec: &Assay, modality: &str) -> Result<ModalityView, String> {
    let libspec = spec
        .get_libspec(modality)
        .ok_or_else(|| format!("modality '{}' not found in library_spec", modality))?;

    let (region_nodes, regions, total_bp) = region_views(&libspec);
    let mut reads = Vec::new();
    for read in spec.get_seqspec(modality) {
        reads.push(project_read(&libspec, &read)?);
    }

    Ok(ModalityView {
        modality: modality.to_string(),
        library_region_id: libspec.region_id.clone(),
        total_bp,
        sequence_protocols: seq_protocol_rows(spec.sequence_protocol.as_ref(), modality),
        sequence_kits: seq_kit_rows(spec.sequence_kit.as_ref(), modality),
        library_protocols: lib_protocol_rows(spec.library_protocol.as_ref(), modality),
        library_kits: lib_kit_rows(spec.library_kit.as_ref(), modality),
        region_nodes,
        regions,
        reads,
    })
}

fn region_views(libspec: &Region) -> (Vec<RegionView>, Vec<RegionView>, i64) {
    walk_regions(&libspec.regions, 0, 0, None, Vec::new(), Vec::new())
}

fn walk_regions(
    regions: &[Region],
    depth: usize,
    bp_start: i64,
    parent_region_id: Option<String>,
    path_region_ids: Vec<String>,
    path_names: Vec<String>,
) -> (Vec<RegionView>, Vec<RegionView>, i64) {
    let mut region_nodes = Vec::new();
    let mut leaf_regions = Vec::new();
    let mut current_bp = bp_start;

    for region in regions {
        let mut region_path_ids = path_region_ids.clone();
        region_path_ids.push(region.region_id.clone());
        let mut region_path_names = path_names.clone();
        region_path_names.push(region.name.clone());
        let start = current_bp;

        if region.regions.is_empty() {
            let end = start + region.max_len;
            let node = build_region_node(
                region,
                depth,
                parent_region_id.clone(),
                region_path_ids,
                region_path_names,
                start,
                end,
            );
            current_bp = end;
            region_nodes.push(node.clone());
            leaf_regions.push(node);
        } else {
            let (child_nodes, child_leaves, next_bp) = walk_regions(
                &region.regions,
                depth + 1,
                current_bp,
                Some(region.region_id.clone()),
                region_path_ids.clone(),
                region_path_names.clone(),
            );
            current_bp = next_bp;
            let node = build_region_node(
                region,
                depth,
                parent_region_id.clone(),
                region_path_ids,
                region_path_names,
                start,
                current_bp,
            );
            region_nodes.push(node);
            region_nodes.extend(child_nodes);
            leaf_regions.extend(child_leaves);
        }
    }

    (region_nodes, leaf_regions, current_bp)
}

fn build_region_node(
    region: &Region,
    depth: usize,
    parent_region_id: Option<String>,
    path_region_ids: Vec<String>,
    path_names: Vec<String>,
    start: i64,
    end: i64,
) -> RegionView {
    RegionView {
        region_id: region.region_id.clone(),
        region_type: region.region_type.clone(),
        name: region.name.clone(),
        sequence_type: region.sequence_type.clone(),
        sequence: region.sequence.clone(),
        min_len: region.min_len,
        max_len: region.max_len,
        len: end - start,
        bp_start: start,
        bp_end: end,
        depth,
        parent_region_id,
        path_region_ids,
        path_names,
        is_leaf: region.regions.is_empty(),
        child_region_ids: region
            .regions
            .iter()
            .map(|child| child.region_id.clone())
            .collect(),
        onlist: onlist_view(region.onlist.clone()),
    }
}

fn project_read(libspec: &Region, read: &Read) -> Result<ReadView, String> {
    let leaves = libspec.get_leaves_with_region_id(&read.primer_id);
    let primer_index = leaves
        .iter()
        .position(|leaf| leaf.region_id == read.primer_id)
        .ok_or_else(|| {
            format!(
                "primer_id '{}' not found in library '{}'",
                read.primer_id, libspec.region_id
            )
        })?;
    let cuts = utils::project_regions_to_coordinates(leaves);
    let primer = &cuts[primer_index];

    let (start, end) = if read.strand == "pos" {
        let start = primer.stop;
        (start, start + read.max_len)
    } else {
        let end = primer.start;
        (end - read.max_len, end)
    };

    Ok(ReadView {
        read_id: read.read_id.clone(),
        name: read.name.clone(),
        label: read.name.clone(),
        primer_id: read.primer_id.clone(),
        min_len: read.min_len,
        max_len: read.max_len,
        strand: read.strand.clone(),
        start,
        end,
        files: read.files.iter().map(file_view).collect(),
    })
}

fn onlist_view(onlist: Option<Onlist>) -> Option<OnlistView> {
    onlist.map(|onlist| OnlistView {
        file_id: onlist.file_id,
        filename: onlist.filename,
        filetype: onlist.filetype,
        filesize: onlist.filesize,
        url: onlist.url,
        urltype: onlist.urltype,
        md5: onlist.md5,
    })
}

fn file_view(file: &File) -> FileView {
    FileView {
        file_id: file.file_id.clone(),
        filename: file.filename.clone(),
        filetype: file.filetype.clone(),
        filesize: file.filesize,
        url: file.url.clone(),
        urltype: file.urltype.clone(),
        md5: file.md5.clone(),
    }
}

fn seq_protocol_rows(entries: Option<&Vec<SeqProtocol>>, modality: &str) -> Vec<MetadataRow> {
    entries
        .map(|entries| {
            entries
                .iter()
                .filter(|entry| entry.modality == modality)
                .map(|entry| MetadataRow {
                    protocol_id: Some(entry.protocol_id.clone()),
                    kit_id: None,
                    name: Some(entry.name.clone()),
                })
                .collect()
        })
        .unwrap_or_default()
}

fn seq_kit_rows(entries: Option<&Vec<SeqKit>>, modality: &str) -> Vec<MetadataRow> {
    entries
        .map(|entries| {
            entries
                .iter()
                .filter(|entry| entry.modality == modality)
                .map(|entry| MetadataRow {
                    protocol_id: None,
                    kit_id: Some(entry.kit_id.clone()),
                    name: entry.name.clone(),
                })
                .collect()
        })
        .unwrap_or_default()
}

fn lib_protocol_rows(entries: Option<&Vec<LibProtocol>>, modality: &str) -> Vec<MetadataRow> {
    entries
        .map(|entries| {
            entries
                .iter()
                .filter(|entry| entry.modality == modality)
                .map(|entry| MetadataRow {
                    protocol_id: Some(entry.protocol_id.clone()),
                    kit_id: None,
                    name: Some(entry.name.clone()),
                })
                .collect()
        })
        .unwrap_or_default()
}

fn lib_kit_rows(entries: Option<&Vec<LibKit>>, modality: &str) -> Vec<MetadataRow> {
    entries
        .map(|entries| {
            entries
                .iter()
                .filter(|entry| entry.modality == modality)
                .map(|entry| MetadataRow {
                    protocol_id: None,
                    kit_id: Some(entry.kit_id.clone()),
                    name: entry.name.clone(),
                })
                .collect()
        })
        .unwrap_or_default()
}

fn escape_script_json(value: &str) -> String {
    value.replace("</", "<\\/")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::read::Read;
    use crate::models::region::Region;
    use crate::utils::load_spec;
    use std::path::PathBuf;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    fn nested_spec() -> Assay {
        let fixed_a = Region::new(
            "fixed_a".into(),
            "linker".into(),
            "fixed a".into(),
            "fixed".into(),
            "AAA".into(),
            3,
            3,
            None,
            vec![],
        );
        let fixed_t = Region::new(
            "fixed_t".into(),
            "linker".into(),
            "fixed t".into(),
            "fixed".into(),
            "T".into(),
            1,
            1,
            None,
            vec![],
        );
        let joined_block = Region::new(
            "joined_block".into(),
            "named".into(),
            "joined block".into(),
            "joined".into(),
            "AAAT".into(),
            4,
            4,
            None,
            vec![fixed_a, fixed_t],
        );
        let umi = Region::new(
            "umi".into(),
            "umi".into(),
            "umi".into(),
            "random".into(),
            "XX".into(),
            2,
            2,
            None,
            vec![],
        );
        let libspec = Region::new(
            "rna".into(),
            "rna".into(),
            "rna".into(),
            "joined".into(),
            "AAATXX".into(),
            6,
            6,
            None,
            vec![joined_block, umi],
        );
        let read = Read::new(
            "rna_R1".into(),
            "Read 1".into(),
            "rna".into(),
            "joined_block".into(),
            2,
            2,
            "pos".into(),
            vec![],
        );
        Assay::new(
            "nested-assay".into(),
            "Nested Assay".into(),
            "".into(),
            "2026-03-24".into(),
            "nested regions".into(),
            vec!["rna".into()],
            "".into(),
            vec![read],
            vec![libspec],
            None,
            None,
            None,
            None,
            Some("0.4.0".into()),
        )
    }

    #[test]
    fn test_build_seqspec_view_data_contains_modalities() {
        let payload = build_seqspec_view_data(&dogma_spec()).unwrap();
        assert_eq!(payload.assay_id, "DOGMAseq-DIG");
        assert_eq!(payload.modalities.len(), 4);
        assert!(payload
            .modalities
            .iter()
            .any(|modality| modality.modality == "rna"));
    }

    #[test]
    fn test_build_seqspec_view_data_projects_reads() {
        let payload = build_seqspec_view_data(&dogma_spec()).unwrap();
        let rna = payload
            .modalities
            .iter()
            .find(|modality| modality.modality == "rna")
            .unwrap();
        let read = rna
            .reads
            .iter()
            .find(|read| read.read_id == "rna_R2")
            .unwrap();
        assert_eq!(read.strand, "neg");
        assert!(read.start < read.end);
        assert_eq!(read.files.len(), 1);
    }

    #[test]
    fn test_render_seqspec_html_contains_payload() {
        let html = render_seqspec_html(&dogma_spec()).unwrap();
        assert!(html.contains("seqspec-view-data"));
        assert!(html.contains("DOGMAseq-DIG"));
        assert!(html.contains("region-rect"));
    }

    #[test]
    fn test_build_seqspec_view_data_keeps_nested_regions() {
        let payload = build_seqspec_view_data(&nested_spec()).unwrap();
        let modality = &payload.modalities[0];
        let parent = modality
            .region_nodes
            .iter()
            .find(|node| node.region_id == "joined_block")
            .unwrap();
        let child = modality
            .region_nodes
            .iter()
            .find(|node| node.region_id == "fixed_a")
            .unwrap();
        assert!(!parent.is_leaf);
        assert_eq!(
            parent.child_region_ids,
            vec!["fixed_a".to_string(), "fixed_t".to_string()]
        );
        assert_eq!(
            child.path_region_ids,
            vec!["joined_block".to_string(), "fixed_a".to_string()]
        );
    }

    #[test]
    fn test_build_seqspec_view_data_projects_reads_from_parent_region() {
        let payload = build_seqspec_view_data(&nested_spec()).unwrap();
        let read = &payload.modalities[0].reads[0];
        assert_eq!(read.primer_id, "joined_block");
        assert_eq!(read.start, 4);
        assert_eq!(read.end, 6);
    }

    #[test]
    fn test_render_seqspec_html_contains_nested_region_payload() {
        let html = render_seqspec_html(&nested_spec()).unwrap();
        assert!(html.contains("joined_block"));
        assert!(html.contains("group-rect"));
    }
}
