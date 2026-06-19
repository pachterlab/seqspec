use crate::models::assay::Assay;
use crate::models::file::File;
use crate::models::region_type::RegionTypeValue;
use crate::utils;
use clap::Args;
use serde_json::Value;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct ModifyArgs {
    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

    #[clap(
        short,
        long,
        help = "Modality of the assay",
        value_name = "MODALITY",
        required = true
    )]
    modality: String,

    #[clap(
        short,
        long,
        help = "JSON array of objects to modify",
        value_name = "KEYS",
        required = true
    )]
    keys: String,

    #[clap(short = 'i', hide = true, value_name = "IDs")]
    legacy_ids: Option<String>,

    #[clap(
        short,
        long,
        help = "Selector",
        value_name = "SELECTOR",
        default_value = "read",
        value_parser = ["read","region","file","seqkit","seqprotocol","libkit","libprotocol","assay"]
    )]
    selector: String,

    #[clap(short, long, help = "Path to output file", value_name = "OUT")]
    output: Option<PathBuf>,
}

pub fn run_modify(args: &ModifyArgs) {
    validate_modify_args(args);
    let mut spec = utils::load_spec(&args.yaml);

    let keys: Vec<Value> = serde_json::from_str(&args.keys).expect("--keys must be a JSON array");
    let selector = args.selector.as_str();
    spec = seqspec_modify(spec, &args.modality, keys, selector);

    spec.update_spec();

    let yaml = spec.to_bytes().unwrap();
    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        f.write_all(&yaml).unwrap();
    } else {
        println!("{}", String::from_utf8_lossy(&yaml));
    }
}

fn validate_modify_args(args: &ModifyArgs) {
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec modify -h` for help.");
        std::process::exit(1);
    }
    if let Some(out) = &args.output {
        if out.exists() && !out.is_file() {
            eprintln!("Output path exists but is not a file: {}", out.display());
            std::process::exit(1);
        }
    }
}

pub fn seqspec_modify(mut spec: Assay, modality: &str, keys: Vec<Value>, selector: &str) -> Assay {
    match selector {
        "read" => modify_reads(&mut spec, modality, &keys),
        "region" => modify_regions(&mut spec, modality, &keys),
        "file" => modify_files(&mut spec, modality, &keys),
        "seqkit" => modify_seqkits(&mut spec, &keys),
        "seqprotocol" => modify_seqprotocols(&mut spec, &keys),
        "libkit" => modify_libkits(&mut spec, &keys),
        "libprotocol" => modify_libprotocols(&mut spec, &keys),
        "assay" => modify_assay(&mut spec, &keys),
        _ => (),
    }
    spec
}

fn vstr(v: &Value, key: &str) -> Option<String> {
    v.get(key).and_then(|x| x.as_str().map(|s| s.to_string()))
}

fn vregion_type(v: &Value, key: &str) -> Option<RegionTypeValue> {
    v.get(key)
        .and_then(|value| serde_json::from_value(value.clone()).ok())
}

fn vi64(v: &Value, key: &str) -> Option<i64> {
    v.get(key).and_then(|x| x.as_i64())
}

fn modify_reads(spec: &mut Assay, modality: &str, keys: &Vec<Value>) {
    for patch in keys {
        let Some(read_id) = vstr(patch, "read_id") else {
            continue;
        };
        if let Some(rd) = spec
            .sequence_spec
            .iter_mut()
            .find(|r| r.modality == modality && r.read_id == read_id)
        {
            // files optional
            let files_opt: Option<Vec<File>> = patch.get("files").and_then(|arr| {
                arr.as_array().map(|items| {
                    items
                        .iter()
                        .filter_map(|it| {
                            Some(File::new(
                                it.get("file_id")?.as_str()?.to_string(),
                                it.get("filename")
                                    .and_then(|x| x.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                                it.get("filetype")
                                    .and_then(|x| x.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                                it.get("filesize").and_then(|x| x.as_i64()).unwrap_or(0),
                                it.get("url")
                                    .and_then(|x| x.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                                it.get("urltype")
                                    .and_then(|x| x.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                                it.get("md5")
                                    .and_then(|x| x.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                            ))
                        })
                        .collect()
                })
            });

            rd.update_read_by_id(
                vstr(patch, "read_id"),
                vstr(patch, "name"),
                vstr(patch, "modality"),
                vstr(patch, "primer_id"),
                vi64(patch, "min_len"),
                vi64(patch, "max_len"),
                vstr(patch, "strand"),
                files_opt,
            );
        }
    }
}

fn modify_regions(spec: &mut Assay, modality: &str, keys: &Vec<Value>) {
    // find index for modality to get mutable region tree
    if let Some(idx) = spec.modalities.iter().position(|m| m == modality) {
        if let Some(target) = spec.library_spec.get_mut(idx) {
            for patch in keys {
                let Some(target_region_id) = vstr(patch, "region_id") else {
                    continue;
                };
                target.update_region_by_id(
                    target_region_id,
                    vstr(patch, "region_id"),
                    vregion_type(patch, "region_type"),
                    vstr(patch, "name"),
                    vstr(patch, "sequence_type"),
                    vstr(patch, "sequence"),
                    vi64(patch, "min_len"),
                    vi64(patch, "max_len"),
                );
            }
        }
    }
}

fn modify_files(spec: &mut Assay, modality: &str, keys: &Vec<Value>) {
    for patch in keys {
        let Some(file_id) = vstr(patch, "file_id") else {
            continue;
        };
        for r in spec
            .sequence_spec
            .iter_mut()
            .filter(|r| r.modality == modality)
        {
            for f in &mut r.files {
                if f.file_id == file_id {
                    if let Some(v) = vstr(patch, "filename") {
                        f.filename = v;
                    }
                    if let Some(v) = vstr(patch, "filetype") {
                        f.filetype = v;
                    }
                    if let Some(v) = vi64(patch, "filesize") {
                        f.filesize = v;
                    }
                    if let Some(v) = vstr(patch, "url") {
                        f.url = v;
                    }
                    if let Some(v) = vstr(patch, "urltype") {
                        f.urltype = v;
                    }
                    if let Some(v) = vstr(patch, "md5") {
                        f.md5 = v;
                    }
                }
            }
        }
    }
}

fn modify_seqkits(spec: &mut Assay, keys: &Vec<Value>) {
    if let Some(kits) = spec.sequence_kit.as_mut() {
        for patch in keys {
            let Some(kit_id) = vstr(patch, "kit_id") else {
                continue;
            };
            if let Some(k) = kits.iter_mut().find(|k| k.kit_id == kit_id) {
                if let Some(v) = vstr(patch, "name") {
                    k.name = Some(v);
                }
                if let Some(v) = vstr(patch, "modality") {
                    k.modality = v;
                }
            }
        }
    }
}

fn modify_seqprotocols(spec: &mut Assay, keys: &Vec<Value>) {
    if let Some(protocols) = spec.sequence_protocol.as_mut() {
        for patch in keys {
            let Some(protocol_id) = vstr(patch, "protocol_id") else {
                continue;
            };
            if let Some(p) = protocols.iter_mut().find(|p| p.protocol_id == protocol_id) {
                if let Some(v) = vstr(patch, "name") {
                    p.name = v;
                }
                if let Some(v) = vstr(patch, "modality") {
                    p.modality = v;
                }
            }
        }
    }
}

fn modify_libkits(spec: &mut Assay, keys: &Vec<Value>) {
    if let Some(kits) = spec.library_kit.as_mut() {
        for patch in keys {
            let Some(kit_id) = vstr(patch, "kit_id") else {
                continue;
            };
            if let Some(k) = kits.iter_mut().find(|k| k.kit_id == kit_id) {
                if let Some(v) = vstr(patch, "name") {
                    k.name = Some(v);
                }
                if let Some(v) = vstr(patch, "modality") {
                    k.modality = v;
                }
            }
        }
    }
}

fn modify_libprotocols(spec: &mut Assay, keys: &Vec<Value>) {
    if let Some(protocols) = spec.library_protocol.as_mut() {
        for patch in keys {
            let Some(protocol_id) = vstr(patch, "protocol_id") else {
                continue;
            };
            if let Some(p) = protocols.iter_mut().find(|p| p.protocol_id == protocol_id) {
                if let Some(v) = vstr(patch, "name") {
                    p.name = v;
                }
                if let Some(v) = vstr(patch, "modality") {
                    p.modality = v;
                }
            }
        }
    }
}

fn modify_assay(spec: &mut Assay, keys: &Vec<Value>) {
    for patch in keys {
        let Some(assay_id) = vstr(patch, "assay_id") else {
            continue;
        };
        if assay_id != spec.assay_id {
            continue;
        }
        if let Some(v) = vstr(patch, "name") {
            spec.name = v;
        }
        if let Some(v) = vstr(patch, "doi") {
            spec.doi = v;
        }
        if let Some(v) = vstr(patch, "date") {
            spec.date = v;
        }
        if let Some(v) = vstr(patch, "description") {
            spec.description = v;
        }
        if let Some(v) = vstr(patch, "lib_struct") {
            spec.lib_struct = v;
        }
        if let Some(v) = vstr(patch, "assay_id") {
            spec.assay_id = v;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;
    use serde_json::json;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_modify_read_name() {
        let spec = dogma_spec();
        let rna_reads = spec.get_seqspec("rna");
        let read_id = rna_reads[0].read_id.clone();
        let keys = vec![json!({"read_id": read_id, "name": "Updated Name"})];
        let modified = seqspec_modify(spec, "rna", keys, "read");
        let read = modified.get_read(&read_id).unwrap();
        assert_eq!(read.name, "Updated Name");
    }

    #[test]
    fn test_modify_region_name() {
        let spec = dogma_spec();
        let lib = spec.get_libspec("rna").unwrap();
        let leaves = lib.get_leaves();
        let target = &leaves[0];
        let keys = vec![json!({"region_id": target.region_id, "name": "New Name"})];
        let modified = seqspec_modify(spec, "rna", keys, "region");
        let lib = modified.get_libspec("rna").unwrap();
        let found = lib.get_region_by_id(&target.region_id);
        assert!(!found.is_empty());
        assert_eq!(found[0].name, "New Name");
    }

    #[test]
    fn test_modify_region_accepts_region_type_list() {
        let spec = dogma_spec();
        let keys = vec![json!({"region_id": "rna_cell_bc", "region_type": ["RGN:partition:cell"]})];
        let modified = seqspec_modify(spec, "rna", keys, "region");
        let region = modified
            .get_libspec("rna")
            .unwrap()
            .get_region_by_id("rna_cell_bc")[0]
            .clone();
        assert!(region.region_type.matches("barcode"));
        assert!(region.region_type.matches("RGN:partition:cell"));
    }

    #[test]
    fn test_modify_file_url() {
        let spec = dogma_spec();
        let rna_reads = spec.get_seqspec("rna");
        // Find a read with files
        let read_with_files = rna_reads.iter().find(|r| !r.files.is_empty());
        if let Some(rd) = read_with_files {
            let file_id = rd.files[0].file_id.clone();
            let keys = vec![json!({"file_id": file_id, "url": "http://new.url/file.fq.gz"})];
            let modified = seqspec_modify(spec, "rna", keys, "file");
            let updated_read = modified.get_read(&rd.read_id).unwrap();
            let f = updated_read
                .files
                .iter()
                .find(|f| f.file_id == file_id)
                .unwrap();
            assert_eq!(f.url, "http://new.url/file.fq.gz");
        }
    }

    #[test]
    fn test_modify_assay_fields() {
        let spec = dogma_spec();
        let assay_id = spec.assay_id.clone();
        let keys = vec![
            json!({"assay_id": assay_id, "name": "New Assay Name", "description": "Updated desc"}),
        ];
        let modified = seqspec_modify(spec, "rna", keys, "assay");
        assert_eq!(modified.name, "New Assay Name");
        assert_eq!(modified.description, "Updated desc");
    }

    #[test]
    fn test_modify_unknown_selector() {
        let spec = dogma_spec();
        let keys = vec![json!({"id": "x"})];
        let modified = seqspec_modify(spec.clone(), "rna", keys, "unknown");
        assert_eq!(modified.assay_id, spec.assay_id);
    }

    #[test]
    fn test_modify_read_preserves_global_read_order() {
        let spec = dogma_spec();
        let original_ids: Vec<String> = spec
            .sequence_spec
            .iter()
            .map(|read| read.read_id.clone())
            .collect();
        let keys = vec![json!({"read_id": "rna_R1", "name": "Updated Name"})];
        let modified = seqspec_modify(spec, "rna", keys, "read");
        let modified_ids: Vec<String> = modified
            .sequence_spec
            .iter()
            .map(|read| read.read_id.clone())
            .collect();
        assert_eq!(modified_ids, original_ids);
    }
}
