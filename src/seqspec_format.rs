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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::assay::Assay;
    use crate::models::region::Region;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    fn leaf(id: &str, seq: &str, stype: &str, len: i64) -> Region {
        Region::new(
            id.into(), "barcode".into(), id.into(), stype.into(),
            seq.into(), len, len, None, vec![],
        )
    }

    fn make_joined(children: Vec<Region>) -> Assay {
        let parent = Region::new(
            "rna".into(), "rna".into(), "rna".into(), "joined".into(),
            "".into(), 0, 0, None, children,
        );
        Assay::new(
            "test".into(), "test".into(), "".into(), "".into(), "".into(),
            vec!["rna".into()], "".into(), vec![], vec![parent],
            None, None, None, None, None,
        )
    }

    #[test]
    fn test_format_updates_joined_parent() {
        let mut spec = make_joined(vec![
            leaf("bc", "ATCG", "fixed", 4),
            leaf("umi", "AACCGG", "fixed", 6),
        ]);
        seqspec_format(&mut spec);
        let lib = spec.get_libspec("rna").unwrap();
        assert_eq!(lib.min_len, 10);
        assert_eq!(lib.max_len, 10);
        assert_eq!(lib.sequence, "ATCGAACCGG");
    }

    #[test]
    fn test_format_random_sequences() {
        let mut spec = make_joined(vec![
            leaf("bc", "", "random", 16),
        ]);
        seqspec_format(&mut spec);
        let lib = spec.get_libspec("rna").unwrap();
        let bc = &lib.regions[0];
        assert_eq!(bc.sequence, "X".repeat(16));
    }

    #[test]
    fn test_format_onlist_sequences() {
        let mut spec = make_joined(vec![
            leaf("bc", "", "onlist", 16),
        ]);
        seqspec_format(&mut spec);
        let lib = spec.get_libspec("rna").unwrap();
        let bc = &lib.regions[0];
        assert_eq!(bc.sequence, "N".repeat(16));
    }

    #[test]
    fn test_format_preserves_fixed() {
        let mut spec = make_joined(vec![
            leaf("linker", "ATCGATCG", "fixed", 8),
        ]);
        seqspec_format(&mut spec);
        let lib = spec.get_libspec("rna").unwrap();
        assert_eq!(lib.regions[0].sequence, "ATCGATCG");
    }

    #[test]
    fn test_format_nested_regions() {
        let inner = Region::new(
            "inner".into(), "inner".into(), "inner".into(), "joined".into(),
            "".into(), 0, 0, None,
            vec![leaf("bc", "ATCG", "fixed", 4), leaf("umi", "AACC", "fixed", 4)],
        );
        let mut spec = make_joined(vec![inner, leaf("linker", "GG", "fixed", 2)]);
        seqspec_format(&mut spec);
        let lib = spec.get_libspec("rna").unwrap();
        assert_eq!(lib.min_len, 10);
        assert_eq!(lib.sequence, "ATCGAACCGG");
    }

    #[test]
    fn test_format_dogma_spec() {
        let mut spec = dogma_spec();
        seqspec_format(&mut spec);
        // All modalities should have well-formed library_spec after format
        for m in spec.list_modalities() {
            let lib = spec.get_libspec(&m).unwrap();
            assert!(lib.min_len > 0, "modality {} should have min_len > 0", m);
        }
    }
}