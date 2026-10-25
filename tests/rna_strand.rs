use seqspec::models::assay::Assay;
use seqspec::models::region::Region;
use seqspec::seqspec_check::seqspec_check_without_external;
use seqspec::seqspec_modify::seqspec_modify;
use seqspec::utils::{get_read_rna_strand, load_spec, load_spec_bytes, map_read_id_to_rna_strands};
use serde_json::json;
use std::path::PathBuf;
use std::process::Command;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn fixture() -> PathBuf {
    repo_root().join("tests/fixtures/rna_strand/spec.yaml")
}

fn spec() -> Assay {
    load_spec(&fixture())
}

fn region_mut<'a>(rgn: &'a mut Region, region_id: &str) -> Option<&'a mut Region> {
    if rgn.region_id == region_id {
        return Some(rgn);
    }
    rgn.regions
        .iter_mut()
        .find_map(|r| region_mut(r, region_id))
}

fn set_rna_strand(spec: &mut Assay, region_id: &str, value: Option<&str>) {
    let lib = &mut spec.library_spec[0];
    region_mut(lib, region_id).unwrap().rna_strand = value.map(str::to_string);
}

fn rna_strand_warnings(spec: &Assay) -> Vec<(String, String, String)> {
    seqspec_check_without_external(spec)
        .into_iter()
        .filter(|d| d.error_type == "check_rna_strand")
        .map(|d| (d.severity, d.error_object, d.error_message))
        .collect()
}

fn read_rna_strand(spec: &Assay, read_id: &str) -> Option<String> {
    get_read_rna_strand(spec, "rna", read_id).unwrap()
}

#[test]
fn load_reads_rna_strand() {
    let spec = spec();
    let lib = spec.get_libspec("rna").unwrap();
    assert_eq!(
        lib.get_region_by_id("cdna")[0].rna_strand.as_deref(),
        Some("antisense")
    );
    assert_eq!(lib.get_region_by_id("barcode")[0].rna_strand, None);
}

#[test]
fn unset_rna_strand_is_not_written() {
    let bytes = spec().to_bytes().unwrap();
    let yaml = String::from_utf8(bytes.clone()).unwrap();
    assert_eq!(yaml.matches("rna_strand").count(), 1);
    let reloaded = load_spec_bytes(&bytes).unwrap();
    let lib = reloaded.get_libspec("rna").unwrap();
    assert_eq!(
        lib.get_region_by_id("cdna")[0].rna_strand.as_deref(),
        Some("antisense")
    );
}

#[test]
fn get_read_rna_strand_truth_table() {
    let cases = [
        (Some("sense"), "pos", Some("sense")),
        (Some("sense"), "neg", Some("antisense")),
        (Some("antisense"), "pos", Some("antisense")),
        (Some("antisense"), "neg", Some("sense")),
        (Some("unstranded"), "pos", Some("unstranded")),
        (Some("unstranded"), "neg", Some("unstranded")),
        (None, "neg", None),
    ];
    for (rna_strand, read_strand, expected) in cases {
        let mut spec = spec();
        set_rna_strand(&mut spec, "cdna", rna_strand);
        let read = spec
            .sequence_spec
            .iter_mut()
            .find(|r| r.read_id == "rna_R2")
            .unwrap();
        read.strand = read_strand.to_string();
        // flip the primer side so the read still faces the cDNA
        if read_strand == "pos" {
            read.primer_id = "umi".to_string();
        }
        assert_eq!(
            read_rna_strand(&spec, "rna_R2").as_deref(),
            expected,
            "rna_strand={rna_strand:?} read strand={read_strand}"
        );
    }
}

#[test]
fn read_without_rna_region_is_unknown() {
    let spec = spec();
    let (_, strands) = map_read_id_to_rna_strands(&spec, "rna", "rna_R1").unwrap();
    assert!(strands.is_empty());
    assert_eq!(read_rna_strand(&spec, "rna_R1"), None);
}

#[test]
fn rna_strand_is_inherited_and_overridden() {
    let mut spec = spec();
    set_rna_strand(&mut spec, "cdna", None);
    set_rna_strand(&mut spec, "rna", Some("sense"));
    let lib = spec.get_libspec("rna").unwrap();
    assert_eq!(
        lib.get_effective_rna_strand("cdna").as_deref(),
        Some("sense")
    );
    assert_eq!(
        read_rna_strand(&spec, "rna_R2").as_deref(),
        Some("antisense")
    );

    set_rna_strand(&mut spec, "cdna", Some("unstranded"));
    let lib = spec.get_libspec("rna").unwrap();
    assert_eq!(
        lib.get_effective_rna_strand("cdna").as_deref(),
        Some("unstranded")
    );
    assert_eq!(
        read_rna_strand(&spec, "rna_R2").as_deref(),
        Some("unstranded")
    );
}

#[test]
fn fixture_has_no_rna_strand_warnings() {
    assert!(rna_strand_warnings(&spec()).is_empty());
}

#[test]
fn check_warns_when_rna_strand_has_no_effect() {
    let mut spec = spec();
    set_rna_strand(&mut spec, "barcode", Some("sense"));
    let warnings = rna_strand_warnings(&spec);
    assert_eq!(warnings.len(), 1);
    let (severity, object, message) = &warnings[0];
    assert_eq!(severity, "warning");
    assert_eq!(object, "region");
    assert!(message.contains("'barcode' sets rna_strand"), "{message}");
}

#[test]
fn check_warns_on_conflicting_rna_strand() {
    // split the cDNA into two leaves that disagree, both covered by R2
    let mut spec = spec();
    let lib = &mut spec.library_spec[0];
    let idx = lib
        .regions
        .iter()
        .position(|r| r.region_id == "cdna")
        .unwrap();
    let cdna = lib.regions[idx].clone();
    let mut first = cdna.clone();
    let mut second = cdna;
    (first.region_id, first.min_len, first.max_len) = ("cdna_a".into(), 2, 2);
    first.sequence = "XX".into();
    (second.region_id, second.min_len, second.max_len) = ("cdna_b".into(), 6, 6);
    second.sequence = "X".repeat(6);
    second.rna_strand = Some("sense".into());
    lib.regions.splice(idx..idx + 1, [first, second]);

    let warnings = rna_strand_warnings(&spec);
    assert_eq!(warnings.len(), 1);
    let (_, object, message) = &warnings[0];
    assert_eq!(object, "read");
    assert!(message.contains("read 'rna_R2'"), "{message}");
    assert!(message.contains("'cdna_a' (antisense)"), "{message}");
    assert!(message.contains("'cdna_b' (sense)"), "{message}");
    assert_eq!(read_rna_strand(&spec, "rna_R2"), None);
}

#[test]
fn check_rejects_invalid_rna_strand_value() {
    let mut spec = spec();
    set_rna_strand(&mut spec, "cdna", Some("forward"));
    assert!(seqspec_check_without_external(&spec)
        .iter()
        .any(|d| d.error_type == "check_schema" && d.error_message.contains("forward")));
}

#[test]
fn modify_sets_and_clears_rna_strand() {
    let cdna = |spec: &Assay| {
        spec.get_libspec("rna").unwrap().get_region_by_id("cdna")[0]
            .rna_strand
            .clone()
    };
    let spec = seqspec_modify(
        spec(),
        "rna",
        vec![json!({"region_id": "cdna", "rna_strand": "sense"})],
        "region",
    );
    assert_eq!(cdna(&spec).as_deref(), Some("sense"));

    // a patch that does not mention rna_strand leaves it alone
    let spec = seqspec_modify(
        spec,
        "rna",
        vec![json!({"region_id": "cdna", "name": "x"})],
        "region",
    );
    assert_eq!(cdna(&spec).as_deref(), Some("sense"));

    let spec = seqspec_modify(
        spec,
        "rna",
        vec![json!({"region_id": "cdna", "rna_strand": null})],
        "region",
    );
    assert_eq!(cdna(&spec), None);
}

#[test]
fn info_rna_strand_cli() {
    let run = |format: &str| {
        let output = Command::new(env!("CARGO_BIN_EXE_seqspec"))
            .args(["info", "-k", "rna_strand", "-f", format])
            .arg(fixture())
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8(output.stdout).unwrap()
    };
    assert_eq!(
        run("tab"),
        "rna\trna_R1\tpos\tunknown\nrna\trna_R2\tneg\tsense\n"
    );
    let rows: serde_json::Value = serde_json::from_str(&run("json")).unwrap();
    assert_eq!(
        rows,
        json!([
            {"modality": "rna", "read_id": "rna_R1", "strand": "pos", "rna_strand": null},
            {"modality": "rna", "read_id": "rna_R2", "strand": "neg", "rna_strand": "sense"},
        ])
    );
}

fn schema_errors(spec: &Assay) -> Vec<String> {
    seqspec_check_without_external(spec)
        .into_iter()
        .filter(|d| d.error_type == "check_schema")
        .map(|d| d.error_message)
        .collect()
}

fn set_cdna_length(spec: &mut Assay, length: i64) {
    // keep the cDNA, its parent, and the read covering it consistent
    let lib = &mut spec.library_spec[0];
    let cdna = region_mut(lib, "cdna").unwrap();
    (cdna.min_len, cdna.max_len, cdna.sequence) = (1, length, "X".into());
    lib.update_attr();
    let read = spec
        .sequence_spec
        .iter_mut()
        .find(|r| r.read_id == "rna_R2")
        .unwrap();
    read.max_len = length;
}

#[test]
fn region_length_allows_long_reads() {
    for length in [2049, 4_000_000, (1 << 30) - 16] {
        let mut spec = spec();
        set_cdna_length(&mut spec, length);
        assert_eq!(
            schema_errors(&spec),
            Vec::<String>::new(),
            "length {length}"
        );
    }
}

#[test]
fn region_length_cap_is_2_to_the_30() {
    let mut spec = spec();
    set_cdna_length(&mut spec, (1 << 30) + 1);
    assert!(schema_errors(&spec)
        .iter()
        .any(|m| m.contains(&(1i64 << 30).to_string())));
}
