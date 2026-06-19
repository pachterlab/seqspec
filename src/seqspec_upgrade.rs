use crate::auth::RemoteAccess;
use crate::models::assay::Assay;
use crate::models::file::File;
use crate::models::onlist::Onlist;
use crate::models::region::Region;
use crate::models::region_type::RegionTypeValue;
use crate::utils;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

const CURRENT_SEQSPEC_VERSION: &str = "0.5.0";

#[derive(Debug, Args)]
pub struct UpgradeArgs {
    #[clap(help = "Path or URL to sequencing specification YAML", required = true)]
    yaml: String,

    #[clap(short, long, help = "Path to output file", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(long, env = "SEQSPEC_AUTH_PROFILE", value_name = "PROFILE")]
    auth_profile: Option<String>,
}

pub fn run_upgrade(args: &UpgradeArgs) {
    let remote_access = RemoteAccess::load(args.auth_profile.as_deref()).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
    validate_upgrade_args(args, &remote_access);
    let spec = utils::load_spec_source(&args.yaml, &remote_access).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
    let version = spec
        .seqspec_version
        .clone()
        .unwrap_or_else(|| "0.0.0".to_string());
    let upgraded = seqspec_upgrade(spec, &version);

    let bytes = upgraded.to_bytes().unwrap();
    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        f.write_all(&bytes).unwrap();
    } else {
        println!("{}", String::from_utf8_lossy(&bytes));
    }
}

fn validate_upgrade_args(args: &UpgradeArgs, remote_access: &RemoteAccess) {
    if let Err(err) = utils::validate_source_exists(&args.yaml, remote_access) {
        eprintln!("{}", err);
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
    let upgraded = match version {
        "0.0.0" => upgrade_0_2_0_to_0_4_0(spec),
        "0.1.0" => upgrade_0_2_0_to_0_4_0(spec),
        "0.1.1" => upgrade_0_2_0_to_0_4_0(spec),
        "0.2.0" => upgrade_0_2_0_to_0_4_0(spec),
        "0.3.0" => upgrade_0_3_0_to_0_4_0(spec),
        "0.4.0" => upgrade_0_4_0_to_0_4_0(spec),
        "0.5.0" => upgrade_0_5_0_to_0_5_0(spec),
        _ => panic!("Unsupported version: {}", version),
    };
    upgrade_region_types_to_0_5_0(upgraded)
}

fn upgrade_region_types_to_0_5_0(spec: Assay) -> Assay {
    fn visit(region: &mut Region) {
        let terms = region.region_type.upgraded_terms();
        region.region_type = RegionTypeValue::from(terms);
        for child in &mut region.regions {
            visit(child);
        }
    }

    let mut spec = spec;
    for region in &mut spec.library_spec {
        visit(region);
    }
    spec.seqspec_version = Some(CURRENT_SEQSPEC_VERSION.to_string());
    spec
}

fn upgrade_0_5_0_to_0_5_0(spec: Assay) -> Assay {
    spec
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
                fn set_onlist_mut(
                    r: &mut crate::models::region::Region,
                    id: &str,
                    new_ol: &Onlist,
                ) {
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
        let upgraded = seqspec_upgrade(spec.clone(), "0.4.0");
        assert_eq!(upgraded.seqspec_version, Some("0.5.0".to_string()));
        assert_eq!(upgraded.modalities, spec.modalities);
        assert_eq!(upgraded.sequence_spec.len(), spec.sequence_spec.len());
    }

    #[test]
    fn test_upgrade_0_3_0_sets_version() {
        let mut spec = dogma_spec();
        spec.seqspec_version = Some("0.3.0".to_string());
        let upgraded = seqspec_upgrade(spec, "0.3.0");
        assert_eq!(upgraded.seqspec_version, Some("0.5.0".to_string()));
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
        assert_eq!(
            upgraded.sequence_spec[0].files[0].file_id,
            upgraded.sequence_spec[0].read_id
        );
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
    fn test_upgrade_sets_version_0_5_0() {
        let mut spec = dogma_spec();
        spec.seqspec_version = Some("0.2.0".to_string());
        let upgraded = seqspec_upgrade(spec, "0.2.0");
        assert_eq!(upgraded.seqspec_version, Some("0.5.0".to_string()));
    }

    #[test]
    fn test_upgrade_loaded_legacy_0_2_spec() {
        let spec = load_spec(&PathBuf::from(
            "tests/fixtures/legacy_0_2_missing_fields.yaml",
        ));
        assert!(spec.sequence_spec[0].files.is_empty());

        let upgraded = seqspec_upgrade(spec, "0.2.0");
        assert_eq!(upgraded.seqspec_version, Some("0.5.0".to_string()));
        assert_eq!(upgraded.sequence_spec[0].files.len(), 1);
        assert_eq!(
            upgraded.sequence_spec[0].files[0].file_id,
            upgraded.sequence_spec[0].read_id
        );

        let barcode = upgraded.library_spec[0]
            .get_region_by_id("barcode")
            .into_iter()
            .next()
            .expect("barcode region");
        let onlist = barcode.onlist.expect("barcode onlist");
        assert_eq!(onlist.file_id, "whitelist.txt.gz");
        assert_eq!(onlist.filename, "whitelist.txt.gz");
        assert_eq!(onlist.md5, "abc123");
    }

    #[test]
    fn test_upgrade_loaded_legacy_0_3_tagged_protocol_spec() {
        let spec = load_spec(&PathBuf::from(
            "tests/fixtures/legacy_0_3_tagged_protocol_objects.yaml",
        ));

        let upgraded = seqspec_upgrade(spec, "0.3.0");
        assert_eq!(upgraded.seqspec_version, Some("0.5.0".to_string()));

        let sequence_kit = upgraded.sequence_kit.expect("sequence kit");
        assert_eq!(sequence_kit.len(), 1);
        assert_eq!(sequence_kit[0].kit_id, "NovaSeq X Series 10B Reagent Kit");

        let library_protocol = upgraded.library_protocol.expect("library protocol");
        assert_eq!(library_protocol.len(), 1);
        assert_eq!(
            library_protocol[0].protocol_id,
            "single-cell RNA sequencing assay (OBI:0002631)"
        );
    }

    #[test]
    fn test_upgrade_converts_region_types_to_ontology_terms() {
        let spec = dogma_spec();
        let upgraded = seqspec_upgrade(spec, "0.4.0");
        let barcode = upgraded.library_spec[0]
            .get_region_by_region_type("barcode")
            .into_iter()
            .next()
            .expect("barcode region");
        assert!(barcode.region_type.has_term("RGN:partition:cell"));
        assert_eq!(barcode.region_type.values(), vec!["RGN:partition:cell"]);
    }

    #[test]
    fn test_upgrade_preserves_index_outputs_for_real_spec() {
        use crate::seqspec_index::{format_index, seqspec_index};

        let spec = dogma_spec();
        let upgraded = seqspec_upgrade(spec.clone(), "0.4.0");
        for tool in ["kb", "simpleaf", "starsolo", "fgbio", "tab"] {
            let modality = "rna".to_string();
            let ids: Vec<String> = Vec::new();
            let idtype = "read".to_string();
            let rev = false;
            let tool = tool.to_string();
            let old = format_index(
                &seqspec_index(&spec, &modality, &ids, &idtype, &rev),
                &tool,
                &None,
            );
            let new = format_index(
                &seqspec_index(&upgraded, &modality, &ids, &idtype, &rev),
                &tool,
                &None,
            );
            assert_eq!(new, old, "tool {tool}");
        }
    }
}
