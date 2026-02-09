use crate::models::assay::Assay;
use crate::models::file::File;
use crate::models::read::Read;
use crate::models::region::Region;
use crate::utils;
use clap::Args;
use serde::Deserialize;
use serde_json::Value;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct InsertArgs {
    #[clap(
        short,
        long,
        help = "Target modality",
        value_name = "MODALITY",
        required = true
    )]
    modality: String,

    #[clap(
        short,
        long,
        help = "Section to insert into",
        value_name = "SELECTOR",
        value_parser = ["region", "read"],
        required = true
    )]
    selector: String,

    #[clap(
        short,
        long,
        help = "Path or inline JSON (expects array of objects)",
        value_name = "IN",
        required = true
    )]
    resource: String,

    #[clap(long, help = "Insert after ID (region or read)")]
    after: Option<String>,

    #[clap(help = "Draft spec to modify", required = true)]
    yaml: PathBuf,

    #[clap(short, long, help = "Write updated spec (default stdout)", value_name = "OUT")]
    output: Option<PathBuf>,
}

pub fn run_insert(args: &InsertArgs) {
    validate_insert_args(args);
    let mut spec = utils::load_spec(&args.yaml);

    let payload = parse_resource(&args.resource);
    match args.selector.as_str() {
        "read" => {
            let reads = load_reads_from_value(&payload, &args.modality);
            spec = seqspec_insert_reads(spec, &args.modality, reads, args.after.as_deref());
        }
        "region" => {
            let regions = load_regions_from_value(&payload);
            spec = seqspec_insert_regions(spec, &args.modality, regions, args.after.as_deref());
        }
        _ => {}
    }

    spec.update_spec();
    let bytes = spec.to_bytes().unwrap();
    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        f.write_all(&bytes).unwrap();
    } else {
        println!("{}", String::from_utf8_lossy(&bytes));
    }
}

fn validate_insert_args(args: &InsertArgs) {
    if args.selector == "region" && matches!(args.after.as_deref(), Some("") ) {
        eprintln!("Invalid --after value");
        std::process::exit(1);
    }
    if !args.yaml.exists() {
        eprintln!("Spec file not found: {}", args.yaml.display());
        std::process::exit(1);
    }
}

fn parse_resource(resource: &str) -> Value {
    // For simplicity, treat resource as inline JSON string (Python parity currently)
    serde_json::from_str(resource).expect("--resource must be a JSON array or object")
}

#[derive(Debug, Deserialize, Clone)]
struct FileInput {
    file_id: Option<String>,
    filename: Option<String>,
    filetype: Option<String>,
    filesize: Option<i64>,
    url: Option<String>,
    urltype: Option<String>,
    md5: Option<String>,
}

impl FileInput {
    fn to_file(&self) -> File {
        let id = self.file_id.clone().or_else(|| self.filename.clone()).unwrap_or_default();
        File::new(
            id,
            self.filename.clone().unwrap_or_default(),
            self.filetype.clone().unwrap_or_default(),
            self.filesize.unwrap_or(0),
            self.url.clone().unwrap_or_default(),
            self.urltype.clone().unwrap_or_default(),
            self.md5.clone().unwrap_or_default(),
        )
    }
}

#[derive(Debug, Deserialize, Clone)]
struct ReadInput {
    read_id: Option<String>,
    name: Option<String>,
    primer_id: Option<String>,
    min_len: Option<i64>,
    max_len: Option<i64>,
    strand: Option<String>,
    files: Option<Vec<FileInput>>,
}

impl ReadInput {
    fn to_read(&self, modality: &str) -> Option<Read> {
        let read_id = self.read_id.clone()?;
        let name = self.name.clone().unwrap_or_else(|| read_id.clone());
        let files = self
            .files
            .as_ref()
            .map(|v| v.iter().map(|f| f.to_file()).collect())
            .unwrap_or_else(|| Vec::new());
        Some(Read::new(
            read_id,
            name,
            modality.to_string(),
            self.primer_id.clone().unwrap_or_default(),
            self.min_len.unwrap_or(0),
            self.max_len.unwrap_or(0),
            self.strand.clone().unwrap_or_else(|| "pos".to_string()),
            files,
        ))
    }
}

#[derive(Debug, Deserialize, Clone)]
struct RegionInput {
    region_id: Option<String>,
    region_type: Option<String>,
    name: Option<String>,
    sequence_type: Option<String>,
    sequence: Option<String>,
    min_len: Option<i64>,
    max_len: Option<i64>,
    regions: Option<Vec<RegionInput>>, // allow nested
}

impl RegionInput {
    fn to_region(&self) -> Option<Region> {
        let region_id = self.region_id.clone()?;
        let name = self.name.clone().unwrap_or_else(|| region_id.clone());
        let children: Vec<Region> = self
            .regions
            .as_ref()
            .map(|v| v.iter().filter_map(|c| c.to_region()).collect())
            .unwrap_or_else(|| Vec::new());
        Some(Region::new(
            region_id,
            self.region_type.clone().unwrap_or_default(),
            name,
            self.sequence_type.clone().unwrap_or_default(),
            self.sequence.clone().unwrap_or_default(),
            self.min_len.unwrap_or(0),
            self.max_len.unwrap_or(0),
            None,
            children,
        ))
    }
}

fn load_reads_from_value(val: &Value, modality: &str) -> Vec<Read> {
    let arr = val.as_array().expect("--resource JSON must be an array of reads");
    let mut out: Vec<Read> = Vec::new();
    for item in arr {
        let ri: ReadInput = serde_json::from_value(item.clone()).expect("Invalid read object");
        if let Some(r) = ri.to_read(modality) { out.push(r); }
    }
    out
}

fn load_regions_from_value(val: &Value) -> Vec<Region> {
    let arr = val.as_array().expect("--resource JSON must be an array of regions");
    let mut out: Vec<Region> = Vec::new();
    for item in arr {
        let ri: RegionInput = serde_json::from_value(item.clone()).expect("Invalid region object");
        if let Some(r) = ri.to_region() { out.push(r); }
    }
    out
}

pub fn seqspec_insert_reads(mut spec: Assay, modality: &str, reads: Vec<Read>, after: Option<&str>) -> Assay {
    let _ = spec.insert_reads(reads, modality, after);
    spec
}

pub fn seqspec_insert_regions(mut spec: Assay, modality: &str, regions: Vec<Region>, after: Option<&str>) -> Assay {
    let _ = spec.insert_regions(regions, modality, after);
    spec
}


