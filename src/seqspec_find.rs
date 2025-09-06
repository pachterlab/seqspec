use crate::utils;
use std::fs;
use std::io::Write;

use clap::Args;
use crate::models::file::File;
use crate::models::read::Read;
use crate::models::region::Region;
use crate::models::assay::Assay;
use serde::{Serialize, Deserialize};
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct FindArgs {
    #[clap(short, long, help = "Output file path", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

    #[clap(
        short,
        long,
        help = "Selector",
        value_name = "SELECTOR",
        required = true,
        value_parser = ["read", "region", "file", "region-type"]
    )]
    selector: String,

    #[clap(
        short,
        long,
        help = "Modality",
        value_name = "MODALITY",
        required = true
    )]
    modality: String,

    #[clap(short, long, help = "ID", value_name = "ID", required = true)]
    id: String,
}

pub fn validate_find_args(args: &FindArgs) -> () {
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec find -h` for help.");
        std::process::exit(1);
    }
    if args.selector.is_empty() {
        eprintln!("Please use `seqspec find -h` for help.");
        std::process::exit(1);
    }
}

pub fn run_find(args: &FindArgs) {
    validate_find_args(args);
    let spec = utils::load_spec(&args.yaml);


    let found = seqspec_find(&spec, &args.selector, &args.modality, &args.id);
    let yaml_str = match found {
        FindResult::Reads(v) => serde_yaml::to_string(&v).unwrap(),
        FindResult::Regions(v) => serde_yaml::to_string(&v).unwrap(),
        FindResult::Files(v) => serde_yaml::to_string(&v).unwrap(),
    };
    // write to output
    if let Some(output) = &args.output {
        let mut file = fs::File::create(output).unwrap();
        writeln!(file, "{}", yaml_str).unwrap();
    } else {
        println!("{}", yaml_str);
    }
}

pub fn find_by_region_type(spec: &Assay, modality: &str, region_type: &str) -> Vec<Region> {
    let m = spec.get_libspec(modality);
    m.unwrap().get_region_by_region_type(region_type)
}

pub fn find_by_region_id(spec: &Assay, modality: &str, region_id: &str) -> Vec<Region> {
    let m = spec.get_libspec(modality);
    match m {
        Some(m) => m.get_region_by_id(region_id),
        None => Vec::new(),
    }
}

pub fn find_by_file_id(spec: &Assay, modality: &str, file_id: &str) -> Vec<File> {
    let m = spec.get_seqspec(modality);
    m.iter()
    .flat_map(|r| r.files.iter())
    .filter(|f| f.file_id == file_id)
    .cloned()
    .collect()
}

pub fn find_by_read_id(spec: &Assay, modality: &str, read_id: &str) -> Vec<Read> {
    let m = spec.get_seqspec(modality);
    m.iter().filter(|r| r.read_id == read_id).cloned().collect()
}


#[derive(Debug, Serialize, Deserialize)]
pub enum FindResult {
    Regions(Vec<Region>),
    Reads(Vec<Read>),
    Files(Vec<File>),
}

pub fn seqspec_find(spec: &Assay, selector: &str, modality: &str, id: &str) -> FindResult {
    match selector {
        "read" => FindResult::Reads(find_by_read_id(spec, modality, id)),
        "region" => FindResult::Regions(find_by_region_id(spec, modality, id)),
        "file" => FindResult::Files(find_by_file_id(spec, modality, id)),
        "region-type" => FindResult::Regions(find_by_region_type(spec, modality, id)),
        _ => panic!("Invalid selector: {}", selector),
    }
}