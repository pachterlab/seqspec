use crate::utils;
use crate::utils::load_spec;
use std::fs::File;
use std::io::Write;
use std::str::FromStr;

use crate::assay::Assay;
use crate::region::Region;
use clap::Args;
use crate::models::file::File;
use crate::models::read::Read;
use crate::models::region::Region;

#[derive(Debug, Args)]
pub struct FindArgs {
    #[clap(short, long, help = "Output file path", value_name = "OUT")]
    output: Option<String>,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: String,

    #[clap(
        short,
        long,
        help = "Selector",
        value_name = "SELECTOR",
        required = true,
        possible_values = &["read", "region", "file", "region-type"]
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
    let fn_ = &args.yaml;
    let m = &args.modality;
    let id = &args.id;
    let o = &args.output;
    let selector = &args.selector;
    let spec = utils::load_spec(&std::path::PathBuf::from_str(fn_).unwrap());

    let regions = if *rt {
        run_find_by_type(&spec, m, r)
    } else {
        run_find(&spec, m, r)
    };

    if let Some(output) = o {
        let mut file = File::create(output).unwrap();
        writeln!(file, "{}", serde_yaml::to_string(&regions).unwrap()).unwrap();
    } else {
        println!("{}", serde_yaml::to_string(&regions).unwrap());
    }
}

pub fn find_by_region_type(spec: &Assay, modality: &str, region_type: &str) -> Vec<Region> {
    let m = spec.get_libspec(modality);
    m.get_region_by_region_type(region_type)
}

pub fn find_by_region_id(spec: &Assay, modality: &str, region_id: &str) -> Vec<Region> {
    let m = spec.get_libspec(modality);
    m.get_region_by_id(region_id)
}

pub fn find_by_file_id(spec: &Assay, modality: &str, file_id: &str) -> Vec<File> {
    let m = spec.get_seqspec(modality);
    m.iter().filter(|r| r.files.iter().any(|f| f.file_id == file_id)).cloned().collect()
}

pub fn find_by_read_id(spec: &Assay, modality: &str, read_id: &str) -> Vec<Read> {
    let m = spec.get_seqspec(modality);
    m.iter().filter(|r| r.read_id == read_id).cloned().collect()
}

pub enum FindResult {
    Regions(Vec<Region>),
    Files(Vec<File>),
    Reads(Vec<Read>),
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