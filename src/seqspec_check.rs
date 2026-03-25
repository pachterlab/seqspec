use crate::auth::RemoteAccess;
use crate::models::assay::Assay;
use crate::models::region::{Region, RegionCoordinate};
use crate::utils;
use clap::Args;
use jsonschema;
use std::collections::HashSet;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Debug, Args)]
pub struct CheckArgs {
    #[clap(short, long, help = "Path to output file", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(
        short,
        long,
        help = "Skip checks",
        value_name = "SKIP",
        default_value = None,
        value_parser = ["igvf", "igvf_onlist_skip", "structural"],
    )]
    skip: Option<String>,

    #[clap(long, env = "SEQSPEC_AUTH_PROFILE", value_name = "PROFILE")]
    auth_profile: Option<String>,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,
}

pub fn run_check(args: &CheckArgs) -> Vec<ErrorObj> {
    validate_check_args(args);
    let spec = utils::load_spec(&args.yaml);
    let remote_access = RemoteAccess::load(args.auth_profile.as_deref()).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
    let errors =
        seqspec_check_with_remote_access(&spec, args.skip.as_deref(), &args.yaml, &remote_access)
            .unwrap_or_else(|err| {
                eprintln!("{}", err);
                std::process::exit(1);
            });

    if let Some(out) = &args.output {
        let mut f = fs::File::create(out).unwrap();
        for (idx, e) in errors.iter().enumerate() {
            writeln!(f, "{}", format_error(e, idx + 1)).unwrap();
        }
    } else {
        for (idx, e) in errors.iter().enumerate() {
            println!("{}", format_error(e, idx + 1));
        }
    }
    errors
}

fn validate_check_args(args: &CheckArgs) {
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

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ErrorObj {
    pub severity: String,
    pub error_type: String,
    pub error_message: String,
    pub error_object: String,
}

fn format_error(e: &ErrorObj, idx: usize) -> String {
    format!("[{} {}] {}", e.severity, idx, e.error_message)
}

pub fn seqspec_check(spec: &Assay, filter_type: Option<&str>, spec_path: &Path) -> Vec<ErrorObj> {
    let access = RemoteAccess::anonymous();
    let mut errors = check(spec, spec_path, &access).unwrap();
    if let Some(ft) = filter_type {
        errors = filter_errors(errors, ft);
    }
    errors
}

pub fn seqspec_check_with_remote_access(
    spec: &Assay,
    filter_type: Option<&str>,
    spec_path: &Path,
    remote_access: &RemoteAccess,
) -> anyhow::Result<Vec<ErrorObj>> {
    let mut errors = check(spec, spec_path, remote_access)?;
    if let Some(ft) = filter_type {
        errors = filter_errors(errors, ft);
    }
    Ok(errors)
}

/// All error_type values produced by structural (non-filesystem) checks.
const STRUCTURAL_CHECK_TYPES: &[&str] = &[
    "check_unique_modalities",
    "check_region_ids_modalities",
    "check_unique_read_ids",
    "check_unique_read_primer_strand_pairs",
    "check_unique_region_ids",
    "check_read_modalities",
    "check_primer_ids_in_region_ids",
    "check_sequence_types",
    "check_region_lengths",
    "check_sequence_lengths",
    "check_read_file_count",
    "check_region_against_subregion_length",
    "check_region_against_subregion_sequence",
    "check_read_length_against_library",
    "check_overlapping_read_regions",
];

fn filter_errors(errors: Vec<ErrorObj>, filter_type: &str) -> Vec<ErrorObj> {
    if filter_type == "structural" {
        return errors
            .into_iter()
            .filter(|e| !STRUCTURAL_CHECK_TYPES.contains(&e.error_type.as_str()))
            .collect();
    }

    let igvf_filters = vec![
        ("check_schema", "'lib_struct'"),
        ("check_schema", "'library_protocol'"),
        ("check_schema", "'library_kit'"),
        ("check_schema", "'sequence_protocol'"),
        ("check_schema", "'sequence_kit'"),
        ("check_schema", "'md5'"),
    ];
    let igvf_onlist_skip_filters = {
        let mut v = igvf_filters.clone();
        v.push(("check_onlist_files_exist", "onlist"));
        v
    };
    let filters = match filter_type {
        "igvf" => igvf_filters,
        "igvf_onlist_skip" => igvf_onlist_skip_filters,
        _ => vec![],
    };
    if filters.is_empty() {
        return errors;
    }
    errors
        .into_iter()
        .filter(|e| {
            !filters
                .iter()
                .any(|(t, o)| e.error_type == *t && e.error_object == *o)
        })
        .collect()
}

/// Run all structural (non-filesystem) checks on a seqspec.
/// This excludes check_schema, check_onlist_files_exist, and check_read_files_exist
/// which require filesystem access or CARGO_MANIFEST_DIR.
pub fn seqspec_check_structural(spec: &Assay) -> Vec<ErrorObj> {
    let errors: Vec<ErrorObj> = Vec::new();
    let idx = 0usize;

    macro_rules! run {
        ($f:ident, $errors:expr) => {{
            let (e2, _i2) = $f(spec, $errors, idx);
            e2
        }};
    }

    let errors = run!(check_unique_modalities, errors);
    let errors = run!(check_region_ids_modalities, errors);
    let errors = run!(check_unique_read_ids, errors);
    let errors = run!(check_unique_read_primer_strand_pairs, errors);
    let errors = run!(check_unique_region_ids, errors);
    let errors = run!(check_read_modalities, errors);
    let errors = run!(check_primer_ids_in_region_ids, errors);
    let errors = run!(check_sequence_types, errors);
    let errors = run!(check_region_lengths, errors);
    let errors = run!(check_sequence_lengths, errors);
    let errors = run!(check_read_file_count, errors);
    let errors = run!(check_region_against_subregion_length, errors);
    let errors = run!(check_region_against_subregion_sequence, errors);
    let errors = run!(check_read_length_against_library, errors);
    let errors = run!(check_overlapping_read_regions, errors);
    errors
}

fn check(
    spec: &Assay,
    spec_path: &Path,
    remote_access: &RemoteAccess,
) -> anyhow::Result<Vec<ErrorObj>> {
    let errors: Vec<ErrorObj> = Vec::new();
    let idx = 0usize;

    // check_schema
    let (e, _i) = check_schema(spec, errors, idx);
    let mut errors = e;

    // Structural checks
    errors.extend(seqspec_check_structural(spec));

    // Filesystem checks
    let spec_base = spec_path.parent().map(|p| p.to_path_buf());
    let (e_on, _i_on) =
        check_onlist_files_exist(spec, errors, idx, spec_base.as_ref(), remote_access)?;
    errors = e_on;
    let (e_rf, _i_rf) =
        check_read_files_exist(spec, errors, idx, spec_base.as_ref(), remote_access)?;
    errors = e_rf;

    Ok(errors)
}

fn push_diagnostic(
    errors: &mut Vec<ErrorObj>,
    idx: &mut usize,
    severity: &str,
    et: &str,
    msg: String,
    obj: &str,
) {
    errors.push(ErrorObj {
        severity: severity.to_string(),
        error_type: et.to_string(),
        error_message: msg,
        error_object: obj.to_string(),
    });
    *idx += 1;
}

fn push_error(errors: &mut Vec<ErrorObj>, idx: &mut usize, et: &str, msg: String, obj: &str) {
    push_diagnostic(errors, idx, "error", et, msg, obj);
}

fn push_warning(errors: &mut Vec<ErrorObj>, idx: &mut usize, et: &str, msg: String, obj: &str) {
    push_diagnostic(errors, idx, "warning", et, msg, obj);
}

fn check_schema(spec: &Assay, mut errors: Vec<ErrorObj>, mut idx: usize) -> (Vec<ErrorObj>, usize) {
    // Load schema from src/schema/seqspec.schema.json
    let schema_path =
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("src/schema/seqspec.schema.json");
    let schema_str = std::fs::read_to_string(&schema_path).unwrap_or_else(|_| "{}".to_string());
    let schema_json: serde_json::Value =
        serde_json::from_str(&schema_str).unwrap_or(serde_json::json!({}));

    if let Ok(validator) = jsonschema::validator_for(&schema_json) {
        let instance = serde_json::to_value(spec).unwrap_or(serde_json::json!({}));
        for error in validator.iter_errors(&instance) {
            // Convert instance path (JSON Pointer) to bracket notation like Python's
            let pointer = format!("{}", error.instance_path);
            let bracket_path = if pointer.is_empty() {
                "spec".to_string()
            } else {
                let parts: String = pointer
                    .trim_start_matches('/')
                    .split('/')
                    .map(|seg| {
                        if seg.chars().all(|c| c.is_ascii_digit()) {
                            format!("[{}]", seg)
                        } else {
                            format!("[\"{}\"]", seg)
                        }
                    })
                    .collect();
                format!("spec{}", parts)
            };
            let msg = format!("{} in {}", error, bracket_path);
            let last_obj = if bracket_path == "spec" {
                "spec".to_string()
            } else {
                // Extract last segment without brackets/quotes
                let seg = bracket_path.rsplit('[').next().unwrap_or("spec");
                seg.trim_end_matches(']').trim_matches('"').to_string()
            };
            errors.push(ErrorObj {
                severity: "error".to_string(),
                error_type: "check_schema".to_string(),
                error_message: msg,
                error_object: last_obj,
            });
            idx += 1;
        }
    }
    (errors, idx)
}

fn check_unique_modalities(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let set: HashSet<_> = spec.modalities.iter().collect();
    if set.len() != spec.modalities.len() {
        push_error(
            &mut errors,
            &mut idx,
            "check_unique_modalities",
            format!("modalities [{}] are not unique", spec.modalities.join(", ")),
            "modalities",
        );
    }
    (errors, idx)
}

fn check_region_ids_modalities(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let modes: HashSet<String> = spec.modalities.iter().cloned().collect();
    for r in &spec.library_spec {
        if !modes.contains(&r.region_id) {
            push_error(
                &mut errors,
                &mut idx,
                "check_region_ids_modalities",
                format!(
                    "region_id '{}' of the first level of the spec does not correspond to a modality [{}]",
                    r.region_id,
                    spec.modalities.join(", ")
                ),
                "region",
            );
        }
    }
    (errors, idx)
}

fn check_onlist_files_exist(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
    spec_base: Option<&PathBuf>,
    remote_access: &RemoteAccess,
) -> anyhow::Result<(Vec<ErrorObj>, usize)> {
    let mut onlists = Vec::new();
    for m in &spec.modalities {
        if let Some(lib) = spec.get_libspec(m) {
            for r in lib.get_onlist_regions() {
                if let Some(ol) = r.onlist {
                    onlists.push(ol);
                }
            }
        }
    }
    for ol in onlists {
        match ol.urltype.as_str() {
            "local" => {
                let mut candidates: Vec<PathBuf> = Vec::new();
                let locator = utils::local_onlist_locator(&ol);
                let p = PathBuf::from(locator);
                candidates.push(if let Some(base) = spec_base {
                    if p.is_absolute() {
                        p.clone()
                    } else {
                        base.join(&p)
                    }
                } else {
                    p.clone()
                });
                // also try .gz variant
                let gz = PathBuf::from(format!("{}.gz", locator));
                candidates.push(if let Some(base) = spec_base {
                    if gz.is_absolute() {
                        gz.clone()
                    } else {
                        base.join(&gz)
                    }
                } else {
                    gz.clone()
                });
                if !candidates.iter().any(|c| c.exists()) {
                    push_error(
                        &mut errors,
                        &mut idx,
                        "check_onlist_files_exist",
                        format!("{} does not exist", ol.filename),
                        "onlist",
                    );
                }
            }
            "http" | "https" | "ftp" => {
                if ol.url.is_empty() || !remote_access.url_exists(&ol.url)? {
                    push_error(
                        &mut errors,
                        &mut idx,
                        "check_onlist_files_exist",
                        format!("{} does not exist", ol.filename),
                        "onlist",
                    );
                }
            }
            _ => {}
        }
    }
    Ok((errors, idx))
}

fn check_unique_read_ids(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let mut seen: HashSet<String> = HashSet::new();
    for read in &spec.sequence_spec {
        if !seen.insert(read.read_id.clone()) {
            push_error(
                &mut errors,
                &mut idx,
                "check_unique_read_ids",
                format!("read_id '{}' is not unique across all reads", read.read_id),
                "read",
            );
        }
    }
    (errors, idx)
}

fn check_read_files_exist(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
    spec_base: Option<&PathBuf>,
    remote_access: &RemoteAccess,
) -> anyhow::Result<(Vec<ErrorObj>, usize)> {
    for read in &spec.sequence_spec {
        for f in &read.files {
            match f.urltype.as_str() {
                "local" => {
                    let p = PathBuf::from(&f.url);
                    let full = if let Some(base) = spec_base {
                        if p.is_absolute() {
                            p.clone()
                        } else {
                            base.join(&p)
                        }
                    } else {
                        p.clone()
                    };
                    if !full.exists() {
                        push_error(
                            &mut errors,
                            &mut idx,
                            "check_read_files_exist",
                            format!("{} does not exist", f.filename),
                            "file",
                        );
                    }
                }
                "http" | "https" | "ftp" => {
                    if f.url.is_empty() || !remote_access.url_exists(&f.url)? {
                        push_error(
                            &mut errors,
                            &mut idx,
                            "check_read_files_exist",
                            format!("{} does not exist", f.filename),
                            "file",
                        );
                    }
                }
                _ => {}
            }
        }
    }
    Ok((errors, idx))
}

fn check_unique_read_primer_strand_pairs(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let mut seen: HashSet<(String, String)> = HashSet::new();
    for read in &spec.sequence_spec {
        let key = (read.primer_id.clone(), read.strand.clone());
        if !seen.insert(key) {
            push_error(
                &mut errors,
                &mut idx,
                "check_unique_read_primer_strand_pairs",
                format!(
                    "primer_id '{}' and strand '{}' tuple is not unique across all reads",
                    read.primer_id, read.strand
                ),
                "read",
            );
        }
    }
    (errors, idx)
}

fn check_unique_region_ids(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let modes = &spec.modalities;
    let mut rids: HashSet<String> = HashSet::new();
    for m in modes {
        if let Some(lib) = spec.get_libspec(m) {
            for r in lib.get_leaves() {
                if !rids.insert(r.region_id.clone()) {
                    push_error(
                        &mut errors,
                        &mut idx,
                        "check_unique_region_ids",
                        format!(
                            "region_id '{}' is not unique across all regions",
                            r.region_id
                        ),
                        "region",
                    );
                }
            }
        }
    }
    (errors, idx)
}

fn check_read_modalities(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let modes: HashSet<String> = spec.modalities.iter().cloned().collect();
    for read in &spec.sequence_spec {
        if !modes.contains(&read.modality) {
            push_error(
                &mut errors,
                &mut idx,
                "check_read_modalities",
                format!(
                    "read '{}' modality '{}' does not exist in the modalities",
                    read.read_id, read.modality
                ),
                "read",
            );
        }
    }
    (errors, idx)
}

fn check_primer_ids_in_region_ids(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let modes = &spec.modalities;
    let mut rids: HashSet<String> = HashSet::new();
    for m in modes {
        if let Some(lib) = spec.get_libspec(m) {
            for r in lib.get_leaves() {
                rids.insert(r.region_id);
            }
        }
    }
    for read in &spec.sequence_spec {
        if !rids.contains(&read.primer_id) {
            push_error(
                &mut errors,
                &mut idx,
                "check_primer_ids_in_region_ids",
                format!(
                    "'{}' primer_id '{}' does not exist in the library_spec",
                    read.read_id, read.primer_id
                ),
                "read",
            );
        }
    }
    (errors, idx)
}

fn check_sequence_types(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    fn recurse(r: &Region, errors: &mut Vec<ErrorObj>, idx: &mut usize) {
        if r.sequence_type == "fixed" && !r.regions.is_empty() {
            push_error(
                errors,
                idx,
                "check_sequence_types",
                format!(
                    "'{}' sequence_type is 'fixed' and contains subregions",
                    r.region_id
                ),
                "region",
            );
        }
        if r.sequence_type == "joined" && r.regions.is_empty() {
            push_error(
                errors,
                idx,
                "check_sequence_types",
                format!(
                    "'{}' sequence_type is 'joined' and does not contain subregions",
                    r.region_id
                ),
                "region",
            );
        }
        if r.sequence_type == "random" && !r.regions.is_empty() {
            push_error(
                errors,
                idx,
                "check_sequence_types",
                format!(
                    "'{}' sequence_type is 'random' and contains subregions",
                    r.region_id
                ),
                "region",
            );
        }
        if r.sequence_type == "random" {
            let all_x = r.sequence.chars().all(|c| c == 'X');
            let len_ok = (r.min_len as usize) <= r.sequence.len()
                && r.sequence.len() <= (r.max_len as usize);
            if !(all_x && len_ok) {
                push_error(
                    errors,
                    idx,
                    "check_sequence_types",
                    format!(
                        "'{}' sequence_type is 'random' and sequence is not all X's",
                        r.region_id
                    ),
                    "region",
                );
            }
        }
        for c in &r.regions {
            recurse(c, errors, idx);
        }
    }
    for m in &spec.modalities {
        if let Some(lib) = spec.get_libspec(m) {
            recurse(&lib, &mut errors, &mut idx);
        }
    }
    (errors, idx)
}

fn check_region_lengths(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    fn recurse(r: &Region, errors: &mut Vec<ErrorObj>, idx: &mut usize) {
        for c in &r.regions {
            recurse(c, errors, idx);
        }
        if r.max_len < r.min_len {
            push_error(
                errors,
                idx,
                "check_region_lengths",
                format!("'{}' max_len is less than min_len", r.region_id),
                "region",
            );
        }
    }
    for m in &spec.modalities {
        if let Some(lib) = spec.get_libspec(m) {
            recurse(&lib, &mut errors, &mut idx);
        }
    }
    (errors, idx)
}

fn check_sequence_lengths(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    fn recurse(r: &Region, errors: &mut Vec<ErrorObj>, idx: &mut usize) {
        for c in &r.regions {
            recurse(c, errors, idx);
        }
        if !r.sequence.is_empty() {
            let l = r.sequence.len();
            if !((r.min_len as usize) <= l && l <= (r.max_len as usize)) {
                push_error(
                    errors,
                    idx,
                    "check_sequence_lengths",
                    format!(
                        "'{}' sequence '{}' has length {}, expected range ({}, {})",
                        r.region_id, r.sequence, l, r.min_len, r.max_len
                    ),
                    "region",
                );
            }
        }
    }
    for m in &spec.modalities {
        if let Some(lib) = spec.get_libspec(m) {
            recurse(&lib, &mut errors, &mut idx);
        }
    }
    (errors, idx)
}

fn check_read_file_count(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    let counts: Vec<usize> = spec.sequence_spec.iter().map(|r| r.files.len()).collect();
    let uniq: HashSet<usize> = counts.iter().cloned().collect();
    if uniq.len() != 1 {
        push_error(
            &mut errors,
            &mut idx,
            "check_read_file_count",
            "Reads must have the same number of files".to_string(),
            "read",
        );
    }
    (errors, idx)
}

fn check_region_against_subregion_length(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    fn recurse(r: &Region, errors: &mut Vec<ErrorObj>, idx: &mut usize) {
        if !r.regions.is_empty() {
            let min_sum: i64 = r.regions.iter().map(|s| s.min_len).sum();
            let max_sum: i64 = r.regions.iter().map(|s| s.max_len).sum();
            if r.min_len != min_sum || r.max_len != max_sum {
                push_error(
                    errors,
                    idx,
                    "check_region_against_subregion_length",
                    format!(
                        "Region '{}' min_len/max_len ({}, {}) does not match sum of subregions ({}, {})",
                        r.region_id, r.min_len, r.max_len, min_sum, max_sum
                    ),
                    "region",
                );
            }
            for c in &r.regions {
                recurse(c, errors, idx);
            }
        }
    }
    for m in &spec.modalities {
        if let Some(lib) = spec.get_libspec(m) {
            recurse(&lib, &mut errors, &mut idx);
        }
    }
    (errors, idx)
}

fn check_region_against_subregion_sequence(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    fn recurse(r: &Region, errors: &mut Vec<ErrorObj>, idx: &mut usize) {
        if !r.regions.is_empty() {
            let concat: String = r.regions.iter().map(|s| s.sequence.clone()).collect();
            if r.sequence != concat {
                push_error(
                    errors,
                    idx,
                    "check_region_against_subregion_sequence",
                    format!(
                        "Region '{}' sequence '{}' does not match concatenation of subregions '{}'",
                        r.region_id, r.sequence, concat
                    ),
                    "region",
                );
            }
            for c in &r.regions {
                recurse(c, errors, idx);
            }
        }
    }
    for m in &spec.modalities {
        if let Some(lib) = spec.get_libspec(m) {
            recurse(&lib, &mut errors, &mut idx);
        }
    }
    (errors, idx)
}

fn check_read_length_against_library(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    for read in &spec.sequence_spec {
        let mode = &read.modality;
        let Some(libspec) = spec.get_libspec(mode) else {
            continue;
        };
        let leaves = libspec.get_leaves_with_region_id(&read.primer_id);
        let pidx = leaves.iter().position(|o| o.region_id == read.primer_id);
        let Some(pidx) = pidx else {
            push_error(
                &mut errors,
                &mut idx,
                "check_read_length_against_library",
                format!(
                    "'{}' primer_id '{}' not found in library leaves for modality '{}'",
                    read.read_id, read.primer_id, mode
                ),
                "read",
            );
            continue;
        };

        let elements: Vec<Region> = if read.strand == "pos" {
            leaves[pidx + 1..].to_vec()
        } else {
            leaves[..pidx].to_vec()
        };

        let sum_max: i64 = elements.iter().map(|o| o.max_len).sum();
        if read.max_len > sum_max {
            let where_str = if read.strand == "pos" {
                "after"
            } else {
                "before"
            };
            push_error(
                &mut errors,
                &mut idx,
                "check_read_length_against_library",
                format!(
                    "'{}' max read length (max_len={}) is greater than sequence-able range (max_sum={}) for library elements {} primer '{}'",
                    read.read_id, read.max_len, sum_max, where_str, read.primer_id
                ),
                "read",
            );
        }
    }
    (errors, idx)
}

fn check_overlapping_read_regions(
    spec: &Assay,
    mut errors: Vec<ErrorObj>,
    mut idx: usize,
) -> (Vec<ErrorObj>, usize) {
    for modality in &spec.modalities {
        let reads = spec.get_seqspec(modality);
        let mut projected_reads: Vec<(String, Vec<RegionCoordinate>)> = Vec::new();

        for read in reads {
            let Ok((mapped_read, regions)) =
                utils::map_read_id_to_regions(spec, modality, &read.read_id)
            else {
                continue;
            };

            let region_coordinates = utils::project_regions_to_coordinates(regions);
            let clipped = utils::itx_read(region_coordinates, 0, mapped_read.max_len);
            projected_reads.push((mapped_read.read_id, clipped));
        }

        for left_idx in 0..projected_reads.len() {
            for right_idx in left_idx + 1..projected_reads.len() {
                let (left_read_id, left_regions) = &projected_reads[left_idx];
                let (right_read_id, right_regions) = &projected_reads[right_idx];
                let right_region_ids: HashSet<String> = right_regions
                    .iter()
                    .map(|region| region.region.region_id.clone())
                    .collect();
                let mut shared_region_ids: Vec<String> = Vec::new();
                let mut seen_region_ids: HashSet<String> = HashSet::new();

                for region in left_regions {
                    let region_id = region.region.region_id.clone();
                    if right_region_ids.contains(&region_id)
                        && seen_region_ids.insert(region_id.clone())
                    {
                        shared_region_ids.push(region_id);
                    }
                }

                if shared_region_ids.is_empty() {
                    continue;
                }

                let region_list = shared_region_ids
                    .iter()
                    .map(|region_id| format!("'{}'", region_id))
                    .collect::<Vec<_>>()
                    .join(", ");
                push_warning(
                    &mut errors,
                    &mut idx,
                    "check_overlapping_read_regions",
                    format!(
                        "reads '{}' and '{}' in modality '{}' both cover region(s) {}. Downstream tools may require explicit overlap handling such as `seqspec index --no-overlap`",
                        left_read_id, right_read_id, modality, region_list
                    ),
                    "read",
                );
            }
        }
    }

    (errors, idx)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_check_valid_spec() {
        let spec = dogma_spec();
        let spec_path = PathBuf::from("tests/fixtures/spec.yaml");
        let diagnostics = seqspec_check(&spec, None, &spec_path);
        // DOGMAseq-DIG is well-formed; only file-existence errors or overlap warnings are expected
        for e in &diagnostics {
            assert!(
                e.error_type == "check_onlist_files_exist"
                    || e.error_type == "check_read_files_exist"
                    || (e.severity == "warning"
                        && e.error_type == "check_overlapping_read_regions"),
                "Unexpected diagnostic type: {} - {}",
                e.error_type,
                e.error_message,
            );
        }
        // No structural/validation error diagnostics
        let structural_errors: Vec<_> = diagnostics
            .iter()
            .filter(|e| {
                e.severity == "error"
                    && e.error_type != "check_onlist_files_exist"
                    && e.error_type != "check_read_files_exist"
            })
            .collect();
        assert!(structural_errors.is_empty());
    }

    #[test]
    fn test_check_onlist_files_exist_prefers_local_url() {
        let spec_path = PathBuf::from("tests/fixtures/onlist_read_clip/spec.yaml");
        let mut spec = load_spec(&spec_path);
        let library = spec.get_libspec("rna").unwrap();
        let barcode = library.get_region_by_id("barcode_a").pop().unwrap();
        let expected_url = barcode.onlist.unwrap().url;

        let barcode_region = spec
            .library_spec
            .get_mut(0)
            .unwrap()
            .regions
            .iter_mut()
            .find(|region| region.region_id == "barcode_a")
            .unwrap();
        barcode_region.onlist.as_mut().unwrap().filename = "display.txt".into();

        let diagnostics = seqspec_check(&spec, None, &spec_path);
        assert!(
            diagnostics.iter().all(|diagnostic| {
                diagnostic.error_type != "check_onlist_files_exist"
                    || !diagnostic.error_message.contains(&expected_url)
            }),
            "local onlist existence should resolve through url before filename"
        );
        assert!(
            diagnostics
                .iter()
                .all(|diagnostic| diagnostic.error_type != "check_onlist_files_exist"),
            "changing the display filename should not trigger an onlist existence error"
        );
    }

    #[test]
    fn test_error_obj_structure() {
        let e = ErrorObj {
            severity: "error".into(),
            error_type: "test_check".into(),
            error_message: "something went wrong".into(),
            error_object: "region".into(),
        };
        assert_eq!(e.severity, "error");
        assert_eq!(e.error_type, "test_check");
        assert_eq!(e.error_message, "something went wrong");
        assert_eq!(e.error_object, "region");
    }

    #[test]
    fn test_filter_errors_igvf() {
        let errors = vec![
            ErrorObj {
                severity: "error".into(),
                error_type: "check_schema".into(),
                error_message: "missing field".into(),
                error_object: "'lib_struct'".into(),
            },
            ErrorObj {
                severity: "error".into(),
                error_type: "check_unique_modalities".into(),
                error_message: "duplicate".into(),
                error_object: "modality".into(),
            },
        ];
        let filtered = filter_errors(errors, "igvf");
        // The check_schema/'lib_struct' error should be filtered out
        assert_eq!(filtered.len(), 1);
        assert_eq!(filtered[0].error_type, "check_unique_modalities");
    }

    #[test]
    fn test_filter_errors_unknown_type() {
        let errors = vec![ErrorObj {
            severity: "error".into(),
            error_type: "test".into(),
            error_message: "msg".into(),
            error_object: "obj".into(),
        }];
        let filtered = filter_errors(errors, "unknown_filter");
        assert_eq!(filtered.len(), 1); // no filtering applied
    }

    #[test]
    fn test_filter_errors_igvf_onlist_skip() {
        let errors = vec![
            ErrorObj {
                severity: "error".into(),
                error_type: "check_schema".into(),
                error_message: "missing field".into(),
                error_object: "'lib_struct'".into(),
            },
            ErrorObj {
                severity: "error".into(),
                error_type: "check_onlist_files_exist".into(),
                error_message: "file missing".into(),
                error_object: "onlist".into(),
            },
            ErrorObj {
                severity: "error".into(),
                error_type: "check_unique_modalities".into(),
                error_message: "duplicate".into(),
                error_object: "modality".into(),
            },
        ];
        let filtered = filter_errors(errors, "igvf_onlist_skip");
        // Both check_schema/'lib_struct' and check_onlist_files_exist/onlist should be filtered
        assert_eq!(filtered.len(), 1);
        assert_eq!(filtered[0].error_type, "check_unique_modalities");
    }

    #[test]
    fn test_check_with_igvf_filter() {
        let spec = dogma_spec();
        let spec_path = PathBuf::from("tests/fixtures/spec.yaml");
        let unfiltered = seqspec_check(&spec, None, &spec_path);
        let filtered = seqspec_check(&spec, Some("igvf"), &spec_path);
        assert!(filtered.len() <= unfiltered.len());
    }

    #[test]
    fn test_check_invalid_spec_duplicate_modalities() {
        use crate::models::region::Region;
        let spec = Assay::new(
            "test".into(),
            "test".into(),
            "".into(),
            "".into(),
            "".into(),
            vec!["rna".into(), "rna".into()], // duplicate
            "".into(),
            vec![],
            vec![
                Region::new(
                    "rna".into(),
                    "rna".into(),
                    "rna".into(),
                    "joined".into(),
                    "".into(),
                    0,
                    0,
                    None,
                    vec![],
                ),
                Region::new(
                    "rna".into(),
                    "rna".into(),
                    "rna".into(),
                    "joined".into(),
                    "".into(),
                    0,
                    0,
                    None,
                    vec![],
                ),
            ],
            None,
            None,
            None,
            None,
            None,
        );
        let spec_path = PathBuf::from("tests/fixtures/spec.yaml");
        let errors = seqspec_check(&spec, None, &spec_path);
        let has_dup = errors
            .iter()
            .any(|e| e.error_type == "check_unique_modalities");
        assert!(has_dup, "Should detect duplicate modalities");
    }

    #[test]
    fn test_check_sequence_types_flags_random_region_with_n_sequence() {
        let spec_path = PathBuf::from("tests/fixtures/random_with_n/spec.yaml");
        let spec = load_spec(&spec_path);
        let errors = seqspec_check(&spec, None, &spec_path);

        assert!(errors.iter().any(|error| {
            error.error_type == "check_sequence_types"
                && error
                    .error_message
                    .contains("'index7' sequence_type is 'random' and sequence is not all X's")
        }));
    }

    #[test]
    fn test_check_warns_on_overlapping_read_regions() {
        let spec_path = PathBuf::from("tests/fixtures/check_overlap_warning/spec.yaml");
        let spec = load_spec(&spec_path);
        let diagnostics = seqspec_check(&spec, None, &spec_path);

        let errors: Vec<_> = diagnostics
            .iter()
            .filter(|diagnostic| diagnostic.severity == "error")
            .collect();
        let warnings: Vec<_> = diagnostics
            .iter()
            .filter(|diagnostic| diagnostic.severity == "warning")
            .collect();

        assert!(errors.is_empty());
        assert_eq!(warnings.len(), 1);
        assert_eq!(warnings[0].error_type, "check_overlapping_read_regions");
        assert!(warnings[0]
            .error_message
            .contains("seqspec index --no-overlap"));
        assert!(warnings[0].error_message.contains("'barcode'"));
        assert!(warnings[0].error_message.contains("'umi'"));
    }
}
