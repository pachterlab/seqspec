use crate::models::assay::{Assay, Codec};
use crate::utils;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct SplitArgs {
    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

    #[clap(
        short,
        long,
        help = "Path to output files",
        value_name = "OUT",
        required = true
    )]
    output: PathBuf,
}

fn validate_split_args(args: &SplitArgs) {
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec split -h` for help.");
        std::process::exit(1);
    }
    if args.output.exists() && args.output.is_file() {
        eprintln!("Output path exists: {}", args.output.display());
        std::process::exit(1);
    }
}

pub fn run_split(args: &SplitArgs) {
    validate_split_args(args);
    let spec = utils::load_spec(&args.yaml);
    let specs = seqspec_split(&spec);

    // Determine prefix (name + "." or "spec.")
    let prefix = args
        .output
        .file_name()
        .and_then(|s| s.to_str())
        .filter(|s| !s.is_empty())
        .map(|s| format!("{}.", s))
        .unwrap_or_else(|| "spec.".to_string());

    // Ensure output directory exists
    let _ = fs::create_dir_all(&args.output);

    for mut spec_m in specs {
        let modality = spec_m.list_modalities().get(0).cloned().unwrap_or_default();
        let out_path = args.output.join(format!("{}{}.yaml", prefix, modality));
        spec_m.update_spec();
        let bytes = spec_m.to_bytes(Codec::Yaml).expect("serialize to YAML");
        let mut f = fs::File::create(out_path).expect("create output file");
        f.write_all(&bytes).expect("write YAML");
    }
}

pub fn seqspec_split(spec: &Assay) -> Vec<Assay> {
    let mut specs: Vec<Assay> = Vec::new();
    let modalities = spec.list_modalities();
    for modality in modalities {
        let sequence_spec = spec.get_seqspec(&modality);
        let library_spec = vec![spec
            .get_libspec(&modality)
            .expect("modality not found in library_spec")];

        let mut spec_m = Assay::new(
            spec.assay_id.clone(),
            spec.name.clone(),
            spec.doi.clone(),
            spec.date.clone(),
            spec.description.clone(),
            vec![modality.clone()],
            spec.lib_struct.clone(),
            sequence_spec,
            library_spec,
            spec.sequence_protocol.clone(),
            spec.sequence_kit.clone(),
            spec.library_protocol.clone(),
            spec.library_kit.clone(),
            spec.seqspec_version.clone(),
        );
        spec_m.update_spec();
        specs.push(spec_m);
    }
    specs
}


