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
    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

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
}

pub fn run_info(args: &InfoArgs) {
    validate_info_args(args);
    let spec = utils::load_spec(&args.yaml);

    let info = seqspec_info(&spec, &args.key);
    let result = format_info(&spec, info, &args.key, &args.format);

    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        writeln!(f, "{}", result).unwrap();
    } else {
        println!("{}", result);
    }
}

fn validate_info_args(args: &InfoArgs) {
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec info -h` for help.");
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
    if let Some(v) = &spec.seqspec_version { m.insert("seqspec_version".to_string(), json!(v)); }
    m.insert("assay_id".to_string(), json!(spec.assay_id));
    m.insert("name".to_string(), json!(spec.name));
    m.insert("doi".to_string(), json!(spec.doi));
    m.insert("date".to_string(), json!(spec.date));
    m.insert("description".to_string(), json!(spec.description));
    m.insert("lib_struct".to_string(), json!(spec.lib_struct));
    if let Some(v) = &spec.library_kit { m.insert("library_kit".to_string(), json!(v)); }
    if let Some(v) = &spec.library_protocol { m.insert("library_protocol".to_string(), json!(v)); }
    if let Some(v) = &spec.sequence_kit { m.insert("sequence_kit".to_string(), json!(v)); }
    if let Some(v) = &spec.sequence_protocol { m.insert("sequence_protocol".to_string(), json!(v)); }
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
    } else { String::new() }
}
fn format_modalities_json(info: &InfoData) -> String {
    if let InfoData::Modalities(v) = info {
        serde_json::to_string_pretty(v).unwrap()
    } else { String::new() }
}

fn format_meta_tab(info: &InfoData) -> String {
    if let InfoData::Meta(v) = info {
        let obj = v.as_object().unwrap();
        let mut vals: Vec<String> = Vec::new();
        for k in [
            "seqspec_version","assay_id","name","doi","date","description","lib_struct","library_kit","library_protocol","sequence_kit","sequence_protocol"
        ] {
            if let Some(val) = obj.get(k) {
                vals.push(if val.is_null() { String::new() } else { val.to_string().trim_matches('"').to_string() });
            }
        }
        vals.join("\t")
    } else { String::new() }
}
fn format_meta_json(info: &InfoData) -> String {
    if let InfoData::Meta(v) = info {
        serde_json::to_string_pretty(v).unwrap()
    } else { String::new() }
}

fn format_sequence_spec_tab(info: &InfoData) -> String {
    if let InfoData::SequenceSpec(reads) = info {
        let mut lines: Vec<String> = Vec::new();
        for r in reads {
            let files = if r.files.is_empty() {
                String::new()
            } else {
                r.files.iter().map(|f| f.file_id.clone()).collect::<Vec<_>>().join(",")
            };
            lines.push(format!(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
                r.modality, r.read_id, r.strand, r.min_len, r.max_len, r.primer_id, r.name, files
            ));
        }
        lines.join("\n")
    } else { String::new() }
}
fn format_sequence_spec_json(info: &InfoData) -> String {
    if let InfoData::SequenceSpec(reads) = info {
        serde_json::to_string_pretty(reads).unwrap()
    } else { String::new() }
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
    } else { String::new() }
}
fn format_library_spec_json(info: &InfoData) -> String {
    if let InfoData::LibrarySpec(map) = info {
        serde_json::to_string_pretty(map).unwrap()
    } else { String::new() }
}


