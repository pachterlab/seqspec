use crate::models::assay::Assay;
use crate::models::file::File;
use crate::models::onlist::Onlist;
use crate::utils;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Args)]
pub struct UpgradeArgs {
    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

    #[clap(short, long, help = "Path to output file", value_name = "OUT")]
    output: Option<PathBuf>,
}

pub fn run_upgrade(args: &UpgradeArgs) {
    validate_upgrade_args(args);
    let spec = utils::load_spec(&args.yaml);
    let version = spec.seqspec_version.clone().unwrap_or_else(|| "0.0.0".to_string());
    let upgraded = seqspec_upgrade(spec, &version);

    let bytes = upgraded.to_bytes().unwrap();
    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        f.write_all(&bytes).unwrap();
    } else {
        println!("{}", String::from_utf8_lossy(&bytes));
    }
}

fn validate_upgrade_args(args: &UpgradeArgs) {
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec upgrade -h` for help.");
        std::process::exit(1);
    }
    if let Some(out) = &args.output {
        if out.exists() && !out.is_file() {
            eprintln!("Output path exists but is not a file: {}", out.display());
            std::process::exit(1);
        }
    }
}

pub fn seqspec_upgrade(spec: Assay, version: &str) -> Assay {
    match version {
        "0.0.0" => upgrade_0_2_0_to_0_4_0(spec),
        "0.1.0" => upgrade_0_2_0_to_0_4_0(spec),
        "0.1.1" => upgrade_0_2_0_to_0_4_0(spec),
        "0.2.0" => upgrade_0_2_0_to_0_4_0(spec),
        "0.3.0" => upgrade_0_3_0_to_0_4_0(spec),
        "0.4.0" => upgrade_0_4_0_to_0_4_0(spec),
        _ => panic!("Unsupported version: {}", version),
    }
}

fn upgrade_0_3_0_to_0_4_0(spec: Assay) -> Assay {
    // 0.3.0 and 0.4.0 are identical
    let mut spec = spec;
    spec.seqspec_version = Some("0.4.0".to_string());
    spec
}

fn upgrade_0_4_0_to_0_4_0(spec: Assay) -> Assay {
    spec
}

fn upgrade_0_2_0_to_0_4_0(spec: Assay) -> Assay {
    let mut spec = spec;
    // ensure reads have files
    for r in &mut spec.sequence_spec {
        if r.files.is_empty() {
            r.update_files(vec![File::new(
                r.read_id.clone(),
                r.read_id.clone(),
                "".to_string(),
                0,
                "".to_string(),
                "".to_string(),
                "".to_string(),
            )]);
        }
    }

    // ensure onlist regions have fully-populated Onlist
    for top in &mut spec.library_spec {
        let leaves = top.get_leaves();
        for lf in leaves {
            if let Some(ol) = &lf.onlist {
                let filename = ol.filename.clone();
                let md5 = ol.md5.clone();
                let new_ol = Onlist {
                    file_id: filename.clone(),
                    filename: filename,
                    filetype: "".to_string(),
                    filesize: 0,
                    url: "".to_string(),
                    urltype: "".to_string(),
                    md5,
                };
                // update the region by id with new onlist fields
                top.update_region_by_id(
                    lf.region_id.clone(),
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                );
                // We cannot directly set onlist via update_region_by_id, so re-find and set
                // Traverse mutably to set onlist on matching leaf
                fn set_onlist_mut(r: &mut crate::models::region::Region, id: &str, new_ol: &Onlist) {
                    if r.region_id == id {
                        r.onlist = Some(new_ol.clone());
                        return;
                    }
                    for c in &mut r.regions {
                        set_onlist_mut(c, id, new_ol);
                    }
                }
                set_onlist_mut(top, &lf.region_id, &new_ol);
            }
        }
    }
    spec.seqspec_version = Some("0.4.0".to_string());
    spec
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
    fn test_upgrade_0_4_0_is_idempotent() {
        let spec = dogma_spec();
        let orig_version = spec.seqspec_version.clone();
        let upgraded = seqspec_upgrade(spec.clone(), "0.4.0");
        assert_eq!(upgraded.seqspec_version, orig_version);
        assert_eq!(upgraded.modalities, spec.modalities);
        assert_eq!(upgraded.sequence_spec.len(), spec.sequence_spec.len());
    }

    #[test]
    fn test_upgrade_0_3_0_sets_version() {
        let mut spec = dogma_spec();
        spec.seqspec_version = Some("0.3.0".to_string());
        let upgraded = seqspec_upgrade(spec, "0.3.0");
        assert_eq!(upgraded.seqspec_version, Some("0.4.0".to_string()));
    }

    #[test]
    fn test_upgrade_0_2_0_adds_files_to_reads() {
        let mut spec = dogma_spec();
        // Remove files from a read to simulate 0.2.0
        spec.sequence_spec[0].files.clear();
        assert!(spec.sequence_spec[0].files.is_empty());
        let upgraded = upgrade_0_2_0_to_0_4_0(spec);
        // After upgrade, the read should have a placeholder file
        assert!(!upgraded.sequence_spec[0].files.is_empty());
        assert_eq!(upgraded.sequence_spec[0].files[0].file_id, upgraded.sequence_spec[0].read_id);
    }

    #[test]
    fn test_upgrade_0_2_0_preserves_existing_files() {
        let spec = dogma_spec();
        let orig_files_len = spec.sequence_spec[0].files.len();
        assert!(orig_files_len > 0);
        let upgraded = upgrade_0_2_0_to_0_4_0(spec);
        // Reads that already had files should keep them unchanged
        assert_eq!(upgraded.sequence_spec[0].files.len(), orig_files_len);
    }

    #[test]
    fn test_upgrade_sets_version_0_4_0() {
        let mut spec = dogma_spec();
        spec.seqspec_version = Some("0.2.0".to_string());
        let upgraded = seqspec_upgrade(spec, "0.2.0");
        assert_eq!(upgraded.seqspec_version, Some("0.4.0".to_string()));
    }
}
