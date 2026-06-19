use serde_yaml::Value;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn unique_temp_dir(name: &str) -> PathBuf {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!("seqspec-{name}-{}-{nanos}", std::process::id()));
    fs::create_dir_all(&dir).unwrap();
    dir
}

fn run_cli(args: &[&str]) -> Output {
    let output = run_cli_raw(args);
    assert!(
        output.status.success(),
        "command failed: {:?}\nstdout:\n{}\nstderr:\n{}",
        args,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    output
}

fn run_cli_raw(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_seqspec"))
        .args(args)
        .current_dir(repo_root())
        .output()
        .unwrap()
}

fn copy_onlist_fixture(dir: &Path) -> PathBuf {
    let fixture_dir = repo_root().join("tests/fixtures/onlist_issue_68");
    for name in ["spec.yaml", "barcode_a.txt", "barcode_b.txt"] {
        fs::copy(fixture_dir.join(name), dir.join(name)).unwrap();
    }
    fs::write(dir.join("rna_read.fastq.gz"), "").unwrap();
    dir.join("spec.yaml")
}

#[test]
fn rust_cli_check_exit_status_tracks_error_diagnostics() {
    let dir = unique_temp_dir("cli-check-exit-status");
    let source = copy_onlist_fixture(&dir);

    let valid = run_cli_raw(&["check", "-s", "igvf_onlist_skip", source.to_str().unwrap()]);
    assert!(
        valid.status.success(),
        "stdout:\n{}\nstderr:\n{}",
        String::from_utf8_lossy(&valid.stdout),
        String::from_utf8_lossy(&valid.stderr)
    );

    let invalid = dir.join("invalid-region-type.yaml");
    let mut data: Value = serde_yaml::from_str(&fs::read_to_string(&source).unwrap()).unwrap();
    data["library_spec"][0]["regions"][0]["region_type"] = Value::Sequence(vec![]);
    fs::write(&invalid, serde_yaml::to_string(&data).unwrap()).unwrap();

    let result = run_cli_raw(&["check", "-s", "igvf_onlist_skip", invalid.to_str().unwrap()]);
    assert_eq!(result.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&result.stdout).contains("region_type"));
}

#[test]
fn rust_cli_region_type_ontology_roundtrip_and_queries() {
    let dir = unique_temp_dir("cli-region-type-onlist");
    let source = copy_onlist_fixture(&dir);
    let upgraded = dir.join("upgraded.yaml");

    run_cli(&[
        "upgrade",
        "-o",
        upgraded.to_str().unwrap(),
        source.to_str().unwrap(),
    ]);

    let upgraded_text = fs::read_to_string(&upgraded).unwrap();
    let upgraded_data: Value = serde_yaml::from_str(&upgraded_text).unwrap();
    assert_eq!(upgraded_data["seqspec_version"].as_str().unwrap(), "0.5.0");
    assert_eq!(
        upgraded_data["library_spec"][0]["regions"][0]["region_type"][0]
            .as_str()
            .unwrap(),
        "RGN:partition:cell"
    );

    let found = run_cli(&[
        "find",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        upgraded.to_str().unwrap(),
    ]);
    let found_text = String::from_utf8(found.stdout).unwrap();
    assert!(!found_text.contains("!!python"));
    let found_regions: Value = serde_yaml::from_str(&found_text).unwrap();
    let region_ids = found_regions
        .as_sequence()
        .unwrap()
        .iter()
        .map(|region| region["region_id"].as_str().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(region_ids, vec!["barcode_a", "barcode_b"]);

    let onlist = run_cli(&[
        "onlist",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        upgraded.to_str().unwrap(),
    ]);
    let onlist_names = String::from_utf8(onlist.stdout)
        .unwrap()
        .lines()
        .map(|line| {
            Path::new(line)
                .file_name()
                .unwrap()
                .to_str()
                .unwrap()
                .to_string()
        })
        .collect::<Vec<_>>();
    assert_eq!(onlist_names, vec!["barcode_b.txt", "barcode_a.txt"]);

    let joined = dir.join("joined.txt");
    run_cli(&[
        "onlist",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        "-f",
        "product",
        "-o",
        joined.to_str().unwrap(),
        upgraded.to_str().unwrap(),
    ]);
    let joined_lines = fs::read_to_string(joined)
        .unwrap()
        .lines()
        .map(str::to_string)
        .collect::<Vec<_>>();
    assert_eq!(joined_lines, vec!["TTAA", "TTAC", "TGAA", "TGAC"]);
}

#[test]
fn rust_cli_region_type_ontology_index_and_file_outputs() {
    let dir = unique_temp_dir("cli-region-type-index");
    let upgraded = dir.join("dogma-upgraded.yaml");
    let source = repo_root().join("tests/fixtures/spec.yaml");

    run_cli(&[
        "upgrade",
        "-o",
        upgraded.to_str().unwrap(),
        source.to_str().unwrap(),
    ]);

    let files = run_cli(&[
        "file",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        "-f",
        "list",
        "-k",
        "file_id",
        upgraded.to_str().unwrap(),
    ]);
    assert_eq!(
        String::from_utf8(files.stdout).unwrap().trim(),
        "rna_cell_bc\tRNA-737K-arc-v1.txt\tRNA-737K-arc-v1.txt"
    );

    let fgbio = run_cli(&[
        "index",
        "-m",
        "rna",
        "-s",
        "read",
        "-i",
        "rna_R1,rna_R2",
        "-t",
        "fgbio",
        upgraded.to_str().unwrap(),
    ]);
    assert_eq!(
        String::from_utf8(fgbio.stdout).unwrap().trim(),
        "16C12M 102T"
    );

    let seqkit = run_cli(&[
        "index",
        "-m",
        "rna",
        "-s",
        "read",
        "-i",
        "rna_R1",
        "--subregion-type",
        "RGN:partition:cell",
        "-t",
        "seqkit",
        upgraded.to_str().unwrap(),
    ]);
    assert_eq!(String::from_utf8(seqkit.stdout).unwrap().trim(), "1:16");
}

#[test]
fn rust_cli_upgrade_legacy_versions_to_region_type_ontology() {
    let dir = unique_temp_dir("cli-region-type-legacy");

    let upgraded_02 = dir.join("legacy-02-upgraded.yaml");
    let source_02 = repo_root().join("tests/fixtures/legacy_0_2_missing_fields.yaml");
    run_cli(&[
        "upgrade",
        "-o",
        upgraded_02.to_str().unwrap(),
        source_02.to_str().unwrap(),
    ]);
    let legacy_02: Value =
        serde_yaml::from_str(&fs::read_to_string(&upgraded_02).unwrap()).unwrap();
    assert_eq!(legacy_02["seqspec_version"].as_str().unwrap(), "0.5.0");
    assert_eq!(
        legacy_02["sequence_spec"][0]["files"][0]["file_id"]
            .as_str()
            .unwrap(),
        "rna_R1"
    );
    assert_eq!(
        legacy_02["library_spec"][0]["regions"][1]["region_type"][0]
            .as_str()
            .unwrap(),
        "RGN:partition:cell"
    );

    let found_barcode = run_cli(&[
        "find",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:cell",
        upgraded_02.to_str().unwrap(),
    ]);
    let found_barcode: Value = serde_yaml::from_slice(&found_barcode.stdout).unwrap();
    let barcode_ids = found_barcode
        .as_sequence()
        .unwrap()
        .iter()
        .map(|region| region["region_id"].as_str().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(barcode_ids, vec!["barcode"]);

    let upgraded_03 = dir.join("legacy-03-upgraded.yaml");
    let source_03 = repo_root().join("tests/fixtures/legacy_0_3_scalar_protocols.yaml");
    run_cli(&[
        "upgrade",
        "-o",
        upgraded_03.to_str().unwrap(),
        source_03.to_str().unwrap(),
    ]);
    let legacy_03: Value =
        serde_yaml::from_str(&fs::read_to_string(&upgraded_03).unwrap()).unwrap();
    assert_eq!(legacy_03["seqspec_version"].as_str().unwrap(), "0.5.0");
    assert_eq!(
        legacy_03["sequence_protocol"][0]["protocol_id"]
            .as_str()
            .unwrap(),
        "NovaSeq"
    );
    assert_eq!(
        legacy_03["library_spec"][0]["regions"][1]["region_type"][0]
            .as_str()
            .unwrap(),
        "RGN:partition:molecule"
    );

    let found_umi = run_cli(&[
        "find",
        "-m",
        "rna",
        "-s",
        "region-type",
        "-i",
        "RGN:partition:molecule",
        upgraded_03.to_str().unwrap(),
    ]);
    let found_umi: Value = serde_yaml::from_slice(&found_umi.stdout).unwrap();
    let umi_ids = found_umi
        .as_sequence()
        .unwrap()
        .iter()
        .map(|region| region["region_id"].as_str().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(umi_ids, vec!["umi"]);
}
