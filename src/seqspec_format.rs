use crate::utils;
use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

use crate::assay::Assay;
use clap::Args;

#[derive(Debug, Args)]
pub struct FormatArgs {
    #[clap(short, long, help = "Output file path", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,
}

pub fn validate_format_args(args: &FormatArgs) -> () {
    // just call the runner and print any error nicely
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec format -h` for help.");
        std::process::exit(1);
    }
}

pub fn run_format(args: &FormatArgs) {
    validate_format_args(args);
    let spec = &mut utils::load_spec(&args.yaml);
    let output = &args.output;
    seqspec_format(spec);
    if let Some(output) = output {
        let mut file = File::create(output).unwrap();
        writeln!(file, "{}", serde_yaml::to_string(&spec).unwrap()).unwrap();
    } else {
        println!("{}", serde_yaml::to_string(&spec).unwrap());
    }
}

fn seqspec_format(spec: &mut Assay) -> () {
    spec.update_spec();
}