use crate::auth::RemoteAccess;
use crate::models::assay::Assay;
use crate::models::read::Read;
use crate::models::region::Region;
use crate::utils;
use clap::Args;
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct InfoArgs {
    #[clap(help = "Path or URL to sequencing specification YAML", required = true)]
    yaml: String,

    #[clap(
        short,
        long,
        help = "Object to display",
        value_name = "KEY",
        default_value = "meta",
        value_parser = ["modalities", "meta", "sequence_spec", "library_spec"]
    )]
    key: String,

    #[clap(
        short,
        long,
        help = "The output format",
        value_name = "FORMAT",
        default_value = "tab",
        value_parser = ["tab", "json"]
    )]
    format: String,

    #[clap(short, long, help = "Path to output file", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(long, env = "SEQSPEC_AUTH_PROFILE", value_name = "PROFILE")]
    auth_profile: Option<String>,
}

pub fn run_info(args: &InfoArgs) {
    let remote_access = RemoteAccess::load(args.auth_profile.as_deref()).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
    validate_info_args(args, &remote_access);
    let spec = utils::load_spec_source(&args.yaml, &remote_access).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });

    let info = seqspec_info(&spec, &args.key);
    let result = format_info(&spec, info, &args.key, &args.format);

    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        writeln!(f, "{}", result).unwrap();
    } else {
        println!("{}", result);
    }
}

fn validate_info_args(args: &InfoArgs, remote_access: &RemoteAccess) {
    if let Err(err) = utils::validate_source_exists(&args.yaml, remote_access) {
        eprintln!("{}", err);
        std::process::exit(1);
    }
    if let Some(out) = &args.output {
        if out.exists() && !out.is_file() {
            eprintln!("Output path exists but is not a file: {}", out.display());
            std::process::exit(1);
        }
    }
}

// ---------------- Core info ----------------

#[derive(Clone)]
enum InfoData {
    Modalities(Vec<String>),
    Meta(Value),
    SequenceSpec(Vec<Read>),
    LibrarySpec(BTreeMap<String, Vec<Region>>),
}

fn seqspec_info(spec: &Assay, key: &str) -> InfoData {
    match key {
        "modalities" => InfoData::Modalities(spec.list_modalities()),
        "meta" => InfoData::Meta(seqspec_info_meta(spec)),
        "sequence_spec" => InfoData::SequenceSpec(spec.sequence_spec.clone()),
        "library_spec" => InfoData::LibrarySpec(seqspec_info_library_spec(spec)),
        _ => panic!("Unsupported info key: {}", key),
    }
}

fn seqspec_info_meta(spec: &Assay) -> Value {
    // preserve a logical, stable order of fields similar to Python's model_dump
    let mut m = serde_json::Map::new();
    if let Some(v) = &spec.seqspec_version {
        m.insert("seqspec_version".to_string(), json!(v));
    }
    m.insert("assay_id".to_string(), json!(spec.assay_id));
    m.insert("name".to_string(), json!(spec.name));
    m.insert("doi".to_string(), json!(spec.doi));
    m.insert("date".to_string(), json!(spec.date));
    m.insert("description".to_string(), json!(spec.description));
    m.insert("lib_struct".to_string(), json!(spec.lib_struct));
    if let Some(v) = &spec.library_kit {
        m.insert("library_kit".to_string(), json!(v));
    }
    if let Some(v) = &spec.library_protocol {
        m.insert("library_protocol".to_string(), json!(v));
    }
    if let Some(v) = &spec.sequence_kit {
        m.insert("sequence_kit".to_string(), json!(v));
    }
    if let Some(v) = &spec.sequence_protocol {
        m.insert("sequence_protocol".to_string(), json!(v));
    }
    Value::Object(m)
}

fn seqspec_info_library_spec(spec: &Assay) -> BTreeMap<String, Vec<Region>> {
    let mut result: BTreeMap<String, Vec<Region>> = BTreeMap::new();
    for m in spec.list_modalities() {
        if let Some(libspec) = spec.get_libspec(&m) {
            let leaves = libspec.get_leaves();
            result.insert(m, leaves);
        }
    }
    result
}

// ---------------- Formatting ----------------

fn format_info(_spec: &Assay, info: InfoData, key: &str, fmt: &str) -> String {
    match (key, fmt) {
        ("modalities", "tab") => format_modalities_tab(&info),
        ("modalities", "json") => format_modalities_json(&info),
        ("meta", "tab") => format_meta_tab(&info),
        ("meta", "json") => format_meta_json(&info),
        ("sequence_spec", "tab") => format_sequence_spec_tab(&info),
        ("sequence_spec", "json") => format_sequence_spec_json(&info),
        ("library_spec", "tab") => format_library_spec_tab(&info),
        ("library_spec", "json") => format_library_spec_json(&info),
        _ => String::new(),
    }
}

fn format_modalities_tab(info: &InfoData) -> String {
    if let InfoData::Modalities(v) = info {
        v.join("\t")
    } else {
        String::new()
    }
}
fn format_modalities_json(info: &InfoData) -> String {
    if let InfoData::Modalities(v) = info {
        serde_json::to_string_pretty(v).unwrap()
    } else {
        String::new()
    }
}

fn format_meta_tab(info: &InfoData) -> String {
    if let InfoData::Meta(v) = info {
        let obj = v.as_object().unwrap();
        let mut vals: Vec<String> = Vec::new();
        for k in [
            "seqspec_version",
            "assay_id",
            "name",
            "doi",
            "date",
            "description",
            "lib_struct",
            "library_kit",
            "library_protocol",
            "sequence_kit",
            "sequence_protocol",
        ] {
            if let Some(val) = obj.get(k) {
                vals.push(if val.is_null() {
                    String::new()
                } else {
                    val.to_string().trim_matches('"').to_string()
                });
            }
        }
        vals.join("\t")
    } else {
        String::new()
    }
}
fn format_meta_json(info: &InfoData) -> String {
    if let InfoData::Meta(v) = info {
        serde_json::to_string_pretty(v).unwrap()
    } else {
        String::new()
    }
}

fn format_sequence_spec_tab(info: &InfoData) -> String {
    if let InfoData::SequenceSpec(reads) = info {
        let mut lines: Vec<String> = Vec::new();
        for r in reads {
            let files = if r.files.is_empty() {
                String::new()
            } else {
                r.files
                    .iter()
                    .map(|f| f.file_id.clone())
                    .collect::<Vec<_>>()
                    .join(",")
            };
            lines.push(format!(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
                r.modality, r.read_id, r.strand, r.min_len, r.max_len, r.primer_id, r.name, files
            ));
        }
        lines.join("\n")
    } else {
        String::new()
    }
}
fn format_sequence_spec_json(info: &InfoData) -> String {
    if let InfoData::SequenceSpec(reads) = info {
        serde_json::to_string_pretty(reads).unwrap()
    } else {
        String::new()
    }
}

fn format_library_spec_tab(info: &InfoData) -> String {
    if let InfoData::LibrarySpec(map) = info {
        let mut lines: Vec<String> = Vec::new();
        for (modality, regions) in map {
            for r in regions {
                let file = r
                    .onlist
                    .as_ref()
                    .map(|o| o.filename.clone())
                    .unwrap_or_else(|| "None".to_string());
                lines.push(format!(
                    "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
                    modality,
                    r.region_id,
                    r.region_type,
                    r.name,
                    r.sequence_type,
                    r.sequence,
                    r.min_len,
                    r.max_len,
                    file
                ));
            }
        }
        lines.join("\n")
    } else {
        String::new()
    }
}
fn format_library_spec_json(info: &InfoData) -> String {
    if let InfoData::LibrarySpec(map) = info {
        serde_json::to_string_pretty(map).unwrap()
    } else {
        String::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_info_modalities() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "modalities");
        if let InfoData::Modalities(v) = info {
            assert!(v.contains(&"rna".to_string()));
            assert!(v.contains(&"atac".to_string()));
            assert_eq!(v.len(), 4);
        } else {
            panic!("Expected Modalities variant");
        }
    }

    #[test]
    fn test_info_meta() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "meta");
        if let InfoData::Meta(v) = info {
            let obj = v.as_object().unwrap();
            assert!(obj.contains_key("assay_id"));
            assert!(obj.contains_key("name"));
            assert_eq!(obj["assay_id"].as_str().unwrap(), "DOGMAseq-DIG");
        } else {
            panic!("Expected Meta variant");
        }
    }

    #[test]
    fn test_info_sequence_spec() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "sequence_spec");
        if let InfoData::SequenceSpec(reads) = info {
            assert_eq!(reads.len(), 9); // 2 RNA + 3 ATAC + 2 Protein + 2 Tag
            let rna_reads: Vec<_> = reads.iter().filter(|r| r.modality == "rna").collect();
            assert_eq!(rna_reads.len(), 2);
            let atac_reads: Vec<_> = reads.iter().filter(|r| r.modality == "atac").collect();
            assert_eq!(atac_reads.len(), 3);
        } else {
            panic!("Expected SequenceSpec variant");
        }
    }

    #[test]
    fn test_info_library_spec() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "library_spec");
        if let InfoData::LibrarySpec(map) = info {
            assert_eq!(map.len(), 4);
            assert_eq!(map["rna"].len(), 5); // 5 RNA leaf regions
            assert_eq!(map["rna"][0].region_id, "rna_truseq_read1");
        } else {
            panic!("Expected LibrarySpec variant");
        }
    }

    #[test]
    fn test_format_modalities_tab() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "modalities");
        let result = format_info(&spec, info, "modalities", "tab");
        let parts: Vec<&str> = result.split('\t').collect();
        assert_eq!(parts.len(), 4);
        assert!(parts.contains(&"rna"));
        assert!(parts.contains(&"atac"));
        assert!(parts.contains(&"protein"));
        assert!(parts.contains(&"tag"));
    }

    #[test]
    fn test_format_meta_json() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "meta");
        let result = format_info(&spec, info, "meta", "json");
        let parsed: Value = serde_json::from_str(&result).unwrap();
        assert!(parsed.is_object());
        assert_eq!(parsed["assay_id"].as_str().unwrap(), "DOGMAseq-DIG");
    }

    #[test]
    fn test_format_meta_tab() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "meta");
        let result = format_info(&spec, info, "meta", "tab");
        let parts: Vec<&str> = result.split('\t').collect();
        // Tab format includes: version, assay_id, name, doi, date, description, lib_struct, ...
        assert!(parts.len() >= 7);
        assert!(parts.contains(&"DOGMAseq-DIG")); // assay_id
        assert!(parts.contains(&"DOGMAseq-DIG")); // name too
    }

    #[test]
    fn test_format_sequence_spec_tab() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "sequence_spec");
        let result = format_info(&spec, info, "sequence_spec", "tab");
        let lines: Vec<&str> = result.lines().collect();
        assert_eq!(lines.len(), 9); // 9 reads total
                                    // First line should be an RNA read
        assert!(
            lines[0].starts_with("rna\t")
                || lines[0].starts_with("protein\t")
                || lines[0].starts_with("tag\t")
                || lines[0].starts_with("atac\t")
        );
        // Check that rna and atac both appear
        let rna_lines = lines.iter().filter(|l| l.starts_with("rna\t")).count();
        assert_eq!(rna_lines, 2);
        let atac_lines = lines.iter().filter(|l| l.starts_with("atac\t")).count();
        assert_eq!(atac_lines, 3);
    }

    #[test]
    fn test_format_sequence_spec_json() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "sequence_spec");
        let result = format_info(&spec, info, "sequence_spec", "json");
        let parsed: Value = serde_json::from_str(&result).unwrap();
        let arr = parsed.as_array().unwrap();
        assert_eq!(arr.len(), 9);
    }

    #[test]
    fn test_format_library_spec_tab() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "library_spec");
        let result = format_info(&spec, info, "library_spec", "tab");
        let lines: Vec<&str> = result.lines().collect();
        // Count lines per modality
        let rna_lines = lines.iter().filter(|l| l.starts_with("rna\t")).count();
        assert_eq!(rna_lines, 5); // 5 RNA leaf regions
    }

    #[test]
    fn test_format_library_spec_json() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "library_spec");
        let result = format_info(&spec, info, "library_spec", "json");
        let parsed: Value = serde_json::from_str(&result).unwrap();
        let obj = parsed.as_object().unwrap();
        assert_eq!(obj.len(), 4);
        assert_eq!(obj["rna"].as_array().unwrap().len(), 5);
    }

    #[test]
    fn test_format_modalities_json() {
        let spec = dogma_spec();
        let info = seqspec_info(&spec, "modalities");
        let result = format_info(&spec, info, "modalities", "json");
        let parsed: Value = serde_json::from_str(&result).unwrap();
        let arr = parsed.as_array().unwrap();
        assert_eq!(arr.len(), 4);
    }
}
