use crate::utils;
use std::fs::File;
use std::io::Write;
use std::str::FromStr;

use crate::assay::Assay;
use clap::Args;

#[derive(Debug, Args)]
pub struct FormatArgs {
    #[clap(short, long, help = "Output file path", value_name = "OUT")]
    output: Option<String>,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: String,
}

pub fn validate_format_args(args: &FormatArgs) -> () {
    // just call the runner and print any error nicely
    if let Err(e) = run_format(args) {
        eprintln!("[error] {e}");
        std::process::exit(1);
    }
}

fn run_format(args: &FormatArgs) -> std::io::Result<()> {
    let spec = &mut utils::load_spec(&std::path::PathBuf::from_str(&args.yaml).unwrap());
    let output = &args.output;
    seqspec_format(spec);
    if let Some(output) = output {
        let mut file = File::create(output).unwrap();
        writeln!(file, "{}", serde_yaml::to_string(&spec).unwrap()).unwrap();
    } else {
        println!("{}", serde_yaml::to_string(&spec).unwrap());
    }
    Ok(())
}

fn seqspec_format(spec: &mut Assay) -> () {
    spec.update_spec();
}