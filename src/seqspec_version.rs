use std::fs::File;
use std::io::{Write};
use std::path::{Path, PathBuf};

use clap::Args;

use crate::models::assay::Assay;
use crate::utils;

/// `seqspec version`
#[derive(Debug, Args)]
pub struct VersionArgs {
    /// Output file path (use '-' for stdout)
    #[clap(short, long, value_name = "OUT")]
    output: Option<PathBuf>,

    /// Sequencing specification YAML file
    #[clap(value_name = "YAML")]
    yaml: PathBuf,
}

pub fn validate_version_args(args: &VersionArgs) {
    // just call the runner and print any error nicely
    if let Err(e) = run_version(args) {
        eprintln!("[error] {e}");
        std::process::exit(1);
    }
}

pub fn run_version(args: &VersionArgs) -> std::io::Result<()> {
    let spec = utils::load_spec(&args.yaml);
    let vinfo = seqspec_version(&spec);
    let out = format_version(&vinfo);

    match args.output.as_deref() {
        // stdout if --output omitted or explicitly '-'
        None => {
            println!("{out}");
        }
        Some(p) if p == Path::new("-") => {
            println!("{out}");
        }
        Some(p) => {
            let mut fh = File::create(p)?;
            writeln!(fh, "{out}")?;
        }
    }
    Ok(())
}

/// Return both tool and file versions
pub fn seqspec_version(spec: &Assay) -> VersionInfo {
    const TOOL_VERSION: &str = env!("CARGO_PKG_VERSION");
    VersionInfo {
        tool_version: TOOL_VERSION.to_string(),
        file_version: spec.seqspec_version.clone().unwrap_or_default(),
    }
}

pub struct VersionInfo {
    pub tool_version: String,
    pub file_version: String,
}

pub fn format_version(v: &VersionInfo) -> String {
    format!(
        "seqspec version: {}\nseqspec file version: {}",
        v.tool_version, v.file_version
    )
}