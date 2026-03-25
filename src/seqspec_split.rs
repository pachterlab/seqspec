use crate::models::assay::Assay;
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
        let bytes = spec_m.to_bytes().expect("serialize to YAML");
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_split_produces_one_per_modality() {
        let spec = dogma_spec();
        let mods = spec.list_modalities();
        let splits = seqspec_split(&spec);
        assert_eq!(splits.len(), mods.len());
    }

    #[test]
    fn test_split_preserves_metadata() {
        let spec = dogma_spec();
        let splits = seqspec_split(&spec);
        for s in &splits {
            assert_eq!(s.assay_id, spec.assay_id);
            assert_eq!(s.name, spec.name);
            assert_eq!(s.doi, spec.doi);
        }
    }

    #[test]
    fn test_split_single_modality_each() {
        let spec = dogma_spec();
        let splits = seqspec_split(&spec);
        for s in &splits {
            assert_eq!(s.modalities.len(), 1);
            assert_eq!(s.library_spec.len(), 1);
        }
    }

    #[test]
    fn test_split_rna_reads_only() {
        let spec = dogma_spec();
        let splits = seqspec_split(&spec);
        let rna_spec = splits.iter().find(|s| s.modalities[0] == "rna").unwrap();
        for r in &rna_spec.sequence_spec {
            assert_eq!(r.modality, "rna");
        }
    }

    #[test]
    fn test_split_atac_reads_only() {
        let spec = dogma_spec();
        let splits = seqspec_split(&spec);
        let atac_spec = splits.iter().find(|s| s.modalities[0] == "atac").unwrap();
        for r in &atac_spec.sequence_spec {
            assert_eq!(r.modality, "atac");
        }
    }

    #[test]
    fn test_split_preserves_total_reads() {
        let spec = dogma_spec();
        let total_reads = spec.sequence_spec.len();
        let splits = seqspec_split(&spec);
        let split_total: usize = splits.iter().map(|s| s.sequence_spec.len()).sum();
        assert_eq!(split_total, total_reads);
    }
}
