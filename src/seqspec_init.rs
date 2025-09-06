use crate::models::assay::{Assay, Codec};
use crate::models::region::Region;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct InitArgs {
    #[clap(short, long, help = "Assay name", required = true)]
    name: String,

    #[clap(
        short,
        long,
        help = "Comma-separated list of modalities (e.g. rna,atac)",
        required = true
    )]
    modalities: String,

    #[clap(long, help = "DOI of the assay", default_value = "")] 
    doi: String,

    #[clap(long, help = "Short description", default_value = "")]
    description: String,

    #[clap(long, help = "Date (YYYY-MM-DD)", default_value = "")]
    date: String,

    #[clap(short, long, help = "Output YAML (default stdout)", value_name = "OUT")]
    output: Option<PathBuf>,
}

pub fn run_init(args: &InitArgs) {
    validate_init_args(args);

    let modalities: Vec<String> = args
        .modalities
        .split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    let mut spec = seqspec_init(
        &args.name,
        &args.doi,
        &args.date,
        &args.description,
        modalities,
    );

    spec.update_spec();

    let yaml = spec
        .to_bytes(Codec::Yaml)
        .expect("Failed to serialize assay to YAML");
    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        f.write_all(&yaml).unwrap();
    } else {
        println!("{}", String::from_utf8_lossy(&yaml));
    }
}

fn validate_init_args(args: &InitArgs) {
    if args.name.is_empty() {
        eprintln!("Assay name is required");
        std::process::exit(1);
    }
    if args.modalities.is_empty() {
        eprintln!("Modalities must be provided");
        std::process::exit(1);
    }
}

pub fn seqspec_init(
    name: &str,
    doi: &str,
    date: &str,
    description: &str,
    modalities: Vec<String>,
) -> Assay {
    let meta_regions: Vec<Region> = modalities
        .iter()
        .map(|modality| {
            Region::new(
                modality.clone(),               // region_id
                "meta".to_string(),            // region_type
                modality.clone(),               // name
                "".to_string(),                // sequence_type
                "".to_string(),                // sequence
                0,                              // min_len
                0,                              // max_len
                None,                           // onlist
                Vec::new(),                     // regions
            )
        })
        .collect();

    Assay::new(
        "".to_string(),               // assay_id
        name.to_string(),
        doi.to_string(),
        date.to_string(),
        description.to_string(),
        modalities,
        "".to_string(),               // lib_struct
        Vec::new(),                    // sequence_spec
        meta_regions,                  // library_spec
        None,                          // sequence_protocol
        None,                          // sequence_kit
        None,                          // library_protocol
        None,                          // library_kit
        None,                          // seqspec_version
    )
}


