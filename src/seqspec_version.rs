use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};

use clap::Args;

use crate::auth::RemoteAccess;
use crate::models::assay::Assay;
use crate::utils;

/// `seqspec version`
#[derive(Debug, Args)]
pub struct VersionArgs {
    /// Output file path (use '-' for stdout)
    #[clap(short, long, value_name = "OUT")]
    output: Option<PathBuf>,

    /// Path or URL to sequencing specification YAML
    #[clap(value_name = "YAML")]
    yaml: String,

    #[clap(long, env = "SEQSPEC_AUTH_PROFILE", value_name = "PROFILE")]
    auth_profile: Option<String>,
}

pub fn validate_version_args(args: &VersionArgs, remote_access: &RemoteAccess) {
    if let Err(err) = utils::validate_source_exists(&args.yaml, remote_access) {
        eprintln!("{}", err);
        std::process::exit(1);
    }
}

pub fn run_version(args: &VersionArgs) {
    let remote_access = RemoteAccess::load(args.auth_profile.as_deref()).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
    validate_version_args(args, &remote_access);
    let spec = utils::load_spec_source(&args.yaml, &remote_access).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
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
            let mut fh = File::create(p).unwrap();
            writeln!(fh, "{out}").unwrap();
        }
    }
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_seqspec_version() {
        let spec = dogma_spec();
        let v = seqspec_version(&spec);
        assert!(!v.tool_version.is_empty());
        assert!(!v.file_version.is_empty());
    }

    #[test]
    fn test_format_version_output() {
        let v = VersionInfo {
            tool_version: "1.0.0".into(),
            file_version: "0.3.0".into(),
        };
        let out = format_version(&v);
        assert!(out.contains("seqspec version: 1.0.0"));
        assert!(out.contains("seqspec file version: 0.3.0"));
    }

    #[test]
    fn test_version_roundtrip() {
        let spec = dogma_spec();
        let v = seqspec_version(&spec);
        let out = format_version(&v);
        assert!(out.contains(&v.tool_version));
        assert!(out.contains(&v.file_version));
    }
}
