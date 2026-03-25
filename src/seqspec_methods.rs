use crate::models::assay::Assay;
use crate::models::file::File as ReadFile;
use crate::models::read::Read;
use crate::models::region::Region;
use crate::utils;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct MethodsArgs {
    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

    #[clap(
        short,
        long,
        help = "Modality",
        value_name = "MODALITY",
        required = true
    )]
    modality: String,

    #[clap(short, long, help = "Path to output file", value_name = "OUT")]
    output: Option<PathBuf>,
}

pub fn run_methods(args: &MethodsArgs) {
    validate_methods_args(args);
    let spec = utils::load_spec(&args.yaml);

    let text = seqspec_methods(&spec, &args.modality);
    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        write!(f, "{}", text).unwrap();
    } else {
        println!("{}", text);
    }
}

fn validate_methods_args(args: &MethodsArgs) {
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec methods -h` for help.");
        std::process::exit(1);
    }
    if let Some(out) = &args.output {
        if out.exists() && !out.is_file() {
            eprintln!("Output path exists but is not a file: {}", out.display());
            std::process::exit(1);
        }
    }
}

pub fn seqspec_methods(spec: &Assay, modality: &str) -> String {
    let mut m = format!(
        "Methods\nThe {} portion of the {} assay was generated on {}.\n    ",
        modality, spec.name, spec.date
    );
    m.push_str(&format_library_spec(spec, modality));
    m
}

fn format_library_spec(spec: &Assay, modality: &str) -> String {
    let leaves = spec
        .get_libspec(modality)
        .expect("modality not found")
        .get_leaves();

    let lib_prot: Option<String> = match &spec.library_protocol {
        Some(v) => v
            .iter()
            .find(|p| p.modality == modality)
            .map(|p| p.protocol_id.clone()),
        None => None,
    };
    let lib_kit: Option<String> = match &spec.library_kit {
        Some(v) => v
            .iter()
            .find(|k| k.modality == modality)
            .map(|k| k.kit_id.clone()),
        None => None,
    };
    let seq_prot: Option<String> = match &spec.sequence_protocol {
        Some(v) => v
            .iter()
            .find(|p| p.modality == modality)
            .map(|p| p.protocol_id.clone()),
        None => None,
    };
    let seq_kit: Option<String> = match &spec.sequence_kit {
        Some(v) => v
            .iter()
            .find(|k| k.modality == modality)
            .map(|k| k.kit_id.clone()),
        None => None,
    };

    let mut s = String::new();
    s.push_str("\nLibary structure\n\n");
    s.push_str(&format!(
        "The library was generated using the {} library protocol and {} library kit. The library contains the following elements:\n\n",
        lib_prot.unwrap_or_else(|| "None".to_string()),
        lib_kit.unwrap_or_else(|| "None".to_string())
    ));
    for (idx, r) in leaves.iter().enumerate() {
        s.push_str(&format_region(r, (idx + 1) as i32));
    }
    s.push_str("\nSequence structure\n\n");
    s.push_str(&format!(
        "The library was sequenced on a {} using the {} sequencing kit. The library was sequenced using the following configuration:\n\n",
        seq_prot.unwrap_or_else(|| "None".to_string()),
        seq_kit.unwrap_or_else(|| "None".to_string())
    ));
    let reads = spec.get_seqspec(modality);
    for (idx, r) in reads.iter().enumerate() {
        s.push_str(&format_read(r, (idx + 1) as i32));
    }
    s
}

fn format_region(region: &Region, idx: i32) -> String {
    let mut s = format!(
        "{}. {}: {}-{}bp {} sequence ({})",
        idx, region.name, region.min_len, region.max_len, region.sequence_type, region.sequence
    );
    if let Some(ol) = &region.onlist {
        s.push_str(&format!(", onlist file: {}.\n", ol.filename));
    } else {
        s.push_str(".\n");
    }
    s
}

fn format_read(read: &Read, idx: i32) -> String {
    let strand = if read.strand == "pos" {
        "positive"
    } else {
        "negative"
    };
    let mut s = format!(
        "- {}: {} cycles on the {} strand using the {} primer. The following files contain the sequences in Read {}:\n",
        read.name, read.max_len, strand, read.primer_id, idx
    );
    if !read.files.is_empty() {
        for (i, f) in read.files.iter().enumerate() {
            s.push_str(&format_read_file(f, (i + 1) as i32));
        }
    }
    s
}

fn format_read_file(file: &ReadFile, idx: i32) -> String {
    format!("- File {}: {}\n", idx, file.filename)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;
    use std::path::PathBuf;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_methods_output_rna() {
        let spec = dogma_spec();
        let text = seqspec_methods(&spec, "rna");
        assert!(text.starts_with("Methods\nThe rna portion of the DOGMAseq-DIG/Illumina assay"));
        assert!(text.contains("Libary structure"));
        assert!(text.contains("Sequence structure"));
        // Should mention the 5 RNA leaf regions
        assert!(text.contains("Cell Barcode"));
        assert!(text.contains("umi"));
        assert!(text.contains("cdna"));
    }

    #[test]
    fn test_format_region() {
        let region = Region::new(
            "bc".into(),
            "barcode".into(),
            "Cell Barcode".into(),
            "onlist".into(),
            "NNNNNNNNNNNNNNNN".into(),
            16,
            16,
            None,
            vec![],
        );
        let s = format_region(&region, 1);
        assert_eq!(
            s,
            "1. Cell Barcode: 16-16bp onlist sequence (NNNNNNNNNNNNNNNN).\n"
        );
    }

    #[test]
    fn test_format_region_with_onlist() {
        let onlist = crate::models::onlist::Onlist::new(
            "ol".into(),
            "barcodes.txt".into(),
            "txt".into(),
            0,
            "".into(),
            "local".into(),
            "".into(),
        );
        let region = Region::new(
            "bc".into(),
            "barcode".into(),
            "Cell Barcode".into(),
            "onlist".into(),
            "N".repeat(16),
            16,
            16,
            Some(onlist),
            vec![],
        );
        let s = format_region(&region, 1);
        assert_eq!(s, "1. Cell Barcode: 16-16bp onlist sequence (NNNNNNNNNNNNNNNN), onlist file: barcodes.txt.\n");
    }

    #[test]
    fn test_format_read() {
        let read = Read::new(
            "R1".into(),
            "Read 1".into(),
            "rna".into(),
            "truseq_read1".into(),
            28,
            28,
            "pos".into(),
            vec![],
        );
        let s = format_read(&read, 1);
        assert_eq!(s, "- Read 1: 28 cycles on the positive strand using the truseq_read1 primer. The following files contain the sequences in Read 1:\n");
    }

    #[test]
    fn test_format_read_file() {
        let f = ReadFile::new(
            "f1".into(),
            "reads_R1.fastq.gz".into(),
            "fastq".into(),
            1024,
            "reads_R1.fastq.gz".into(),
            "local".into(),
            "".into(),
        );
        let s = format_read_file(&f, 1);
        assert_eq!(s, "- File 1: reads_R1.fastq.gz\n");
    }

    #[test]
    fn test_methods_other_modalities() {
        let spec = dogma_spec();
        for modality in ["atac", "protein", "tag"] {
            let text = seqspec_methods(&spec, modality);
            assert!(text.contains("Methods"));
            assert!(text.contains(modality));
        }
    }

    #[test]
    fn test_format_library_spec_sections() {
        let spec = dogma_spec();
        let text = format_library_spec(&spec, "rna");
        assert!(text.contains("Libary structure"));
        assert!(text.contains("Sequence structure"));
        assert!(text.contains("library protocol"));
        assert!(text.contains("sequencing kit"));
    }
}
