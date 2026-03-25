use crate::models::assay::Assay;
use crate::models::region::{Region, RegionCoordinate};
use crate::seqspec_html;
use crate::utils;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct PrintArgs {
    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

    #[clap(short, long, help = "Path to output file", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(
        short,
        long,
        help = "Format",
        value_name = "FORMAT",
        default_value = "library-ascii",
        value_parser = ["library-ascii", "seqspec-ascii", "seqspec-html", "seqspec-png"],
    )]
    format: String,
}

pub fn run_print(args: &PrintArgs) {
    validate_print_args(args);

    let spec = utils::load_spec(&args.yaml);
    let result = seqspec_print(&spec, &args.format).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });

    if let Some(out) = &args.output {
        let mut fh = fs::File::create(out).unwrap();
        writeln!(fh, "{result}").unwrap();
    } else {
        println!("{result}");
    }
}

fn validate_print_args(args: &PrintArgs) {
    if !args.yaml.exists() {
        eprintln!("Input file does not exist: {}", args.yaml.display());
        std::process::exit(1);
    }
    if let Some(out) = &args.output {
        if out.exists() && !out.is_file() {
            eprintln!("Output path exists but is not a file: {}", out.display());
            std::process::exit(1);
        }
    }
}

pub fn seqspec_print(spec: &Assay, fmt: &str) -> Result<String, String> {
    match fmt {
        "library-ascii" => Ok(print_library_ascii(spec)),
        "seqspec-ascii" => print_seqspec_ascii(spec),
        "seqspec-html" => seqspec_html::render_seqspec_html(spec),
        "seqspec-png" => Err("seqspec-png is not implemented in the Rust CLI yet".to_string()),
        _ => Err(format!("Unsupported format: {}", fmt)),
    }
}

fn print_seqspec_ascii(spec: &Assay) -> Result<String, String> {
    let mut parts = Vec::new();
    for modality in &spec.modalities {
        let (p, n) = libseq(spec, modality)?;
        parts.push(format_libseq(spec, modality, p, n)?);
    }
    Ok(parts.join("\n"))
}

fn format_libseq(
    spec: &Assay,
    modality: &str,
    positive: Vec<String>,
    negative: Vec<String>,
) -> Result<String, String> {
    let libspec = spec
        .get_libspec(modality)
        .ok_or_else(|| format!("modality '{}' not found", modality))?;

    Ok([
        modality.to_string(),
        "---".to_string(),
        positive.join("\n"),
        libspec.sequence.clone(),
        utils::complement_seq(&libspec.sequence),
        negative.join("\n"),
    ]
    .join("\n"))
}

fn libseq(spec: &Assay, modality: &str) -> Result<(Vec<String>, Vec<String>), String> {
    let libspec = spec
        .get_libspec(modality)
        .ok_or_else(|| format!("modality '{}' not found", modality))?;
    let seqspec = spec.get_seqspec(modality);

    let mut positive = Vec::new();
    let mut negative = Vec::new();

    for (idx, read) in seqspec.iter().enumerate() {
        let leaves = libspec.get_leaves_with_region_id(&read.primer_id);
        let primer_idx = leaves
            .iter()
            .position(|leaf| leaf.region_id == read.primer_id)
            .ok_or_else(|| {
                format!(
                    "primer_id '{}' not found in modality '{}'",
                    read.primer_id, modality
                )
            })?;

        let cuts: Vec<RegionCoordinate> = utils::project_regions_to_coordinates(leaves);
        let primer_pos = &cuts[primer_idx];
        let arrow_len = read.max_len.saturating_sub(1) as usize;
        let arrow = "-".repeat(arrow_len);

        if read.strand == "pos" {
            let space_len = primer_pos.stop.saturating_sub(1) as usize;
            let ws = " ".repeat(space_len);
            positive.push(format!("{}|{}>({}) {}", ws, arrow, idx + 1, read.read_id));
        } else {
            let space_len = primer_pos.start.saturating_sub(read.max_len) as usize;
            let ws = " ".repeat(space_len);
            negative.push(format!("{}<{}|({}) {}", ws, arrow, idx + 1, read.read_id));
        }
    }

    Ok((positive, negative))
}

fn print_library_ascii(spec: &Assay) -> String {
    spec.library_spec
        .iter()
        .map(|region| render_region_tree(region, "", true))
        .collect::<Vec<_>>()
        .join("\n")
}

fn render_region_tree(region: &Region, prefix: &str, is_last: bool) -> String {
    let branch = if prefix.is_empty() {
        ""
    } else if is_last {
        "└── "
    } else {
        "├── "
    };
    let mut lines = vec![format!(
        "{}{}{}({},{})",
        prefix, branch, region.region_id, region.min_len, region.max_len
    )];

    let child_prefix = if prefix.is_empty() {
        String::new()
    } else if is_last {
        format!("{}    ", prefix)
    } else {
        format!("{}│   ", prefix)
    };

    for (idx, child) in region.regions.iter().enumerate() {
        lines.push(render_region_tree(
            child,
            &child_prefix,
            idx + 1 == region.regions.len(),
        ));
    }

    lines.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_print_library_ascii_contains_modalities_and_regions() {
        let rendered = print_library_ascii(&dogma_spec());
        assert!(rendered.contains("rna("));
        assert!(rendered.contains("rna_cell_bc"));
        assert!(rendered.contains("atac"));
    }

    #[test]
    fn test_print_seqspec_ascii_contains_reads_and_sequence() {
        let rendered = print_seqspec_ascii(&dogma_spec()).unwrap();
        assert!(rendered.contains("rna"));
        assert!(rendered.contains("rna_R1"));
        assert!(rendered.contains("rna_R2"));
        assert!(rendered.contains("---"));
    }

    #[test]
    fn test_print_seqspec_html_contains_payload() {
        let html = seqspec_print(&dogma_spec(), "seqspec-html").unwrap();
        assert!(html.contains("seqspec-view-data"));
        assert!(html.contains("DOGMAseq-DIG"));
    }
}
