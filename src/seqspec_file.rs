use crate::auth::RemoteAccess;
use crate::models::assay::Assay;
use crate::models::file::File;
use crate::models::onlist::Onlist;
use crate::utils;
use clap::Args;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Debug, Args)]
pub struct FileArgs {
    #[clap(short, long, help = "Output file path", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(help = "Path or URL to sequencing specification YAML", required = true)]
    yaml: String,

    #[clap(
        short,
        long,
        help = "IDs",
        value_name = "IDs",
        required = false,
        value_delimiter = ','
    )]
    ids: Option<Vec<String>>,

    #[clap(
        short,
        long,
        help = "Modality",
        value_name = "MODALITY",
        required = true
    )]
    modality: String,

    #[clap(
        short,
        long,
        help = "Selector",
        value_name = "SELECTOR",
        value_parser = ["read", "region", "file", "region-type"],
        default_value = "read"
    )]
    selector: String,

    #[clap(
        short = 'f',
        long,
        help = "Format",
        value_name = "FORMAT",
        value_parser = ["paired", "interleaved", "index", "list", "json"],
        default_value = "paired"
    )]
    format: String,

    #[clap(
        short,
        long,
        help = "Key",
        value_name = "KEY",
        value_parser = ["file_id", "filename", "filetype", "filesize", "url", "urltype", "md5", "all"],
        default_value = "file_id"
    )]
    key: String,

    #[clap(long, help = "Use full path for local urls", default_value = "false")]
    fullpath: bool,

    #[clap(long, env = "SEQSPEC_AUTH_PROFILE", value_name = "PROFILE")]
    auth_profile: Option<String>,
}

pub fn run_file(args: &FileArgs) {
    let remote_access = RemoteAccess::load(args.auth_profile.as_deref()).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
    validate_file_args(args, &remote_access);
    let spec = utils::load_spec_source(&args.yaml, &remote_access).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });
    let spec_base = utils::spec_base_from_source(&args.yaml);

    let ids = args.ids.clone();
    let files = seqspec_file(&spec, &args.modality, ids.as_ref(), &args.selector);

    if !files.is_empty() {
        let result = match args.format.as_str() {
            "list" => format_list_files_metadata(&files, &args.key, spec_base.as_deref(), args.fullpath),
            "paired" | "interleaved" | "index" => format_list_files(
                &files,
                &args.format,
                Some(&args.key),
                spec_base.as_deref(),
                args.fullpath,
            ),
            "json" => format_json_files(&files, &args.key, spec_base.as_deref(), args.fullpath),
            _ => String::new(),
        };

        if let Some(output) = &args.output {
            let mut file = fs::File::create(output).unwrap();
            writeln!(file, "{}", result).unwrap();
        } else {
            println!("{}", result);
        }
    }
}

fn validate_file_args(args: &FileArgs, remote_access: &RemoteAccess) {
    if let Err(err) = utils::validate_source_exists(&args.yaml, remote_access) {
        eprintln!("{}", err);
        std::process::exit(1);
    }
    if ["filesize", "filetype", "urltype", "md5"].contains(&args.key.as_str())
        && ["paired", "interleaved", "index"].contains(&args.format.as_str())
    {
        eprintln!(
            "Format '{}' valid only with key 'file_id', 'filename', or 'url'",
            args.format
        );
        std::process::exit(1);
    }
}

pub fn seqspec_file(
    spec: &Assay,
    modality: &String,
    ids: Option<&Vec<String>>,
    selector: &String,
) -> HashMap<String, Vec<File>> {
    let list_files = |sel: &str| -> HashMap<String, Vec<File>> {
        match sel {
            "read" => list_read_files(spec, modality),
            "region" => list_region_files(spec, modality),
            "file" => list_all_files(spec, modality),
            _ => HashMap::new(),
        }
    };

    let list_files_by_id = |sel: &str, ids: &Vec<String>| -> HashMap<String, Vec<File>> {
        match sel {
            "read" => list_files_by_read_id(spec, modality, ids),
            "file" => list_files_by_file_id(spec, modality, ids),
            "region" => list_files_by_region_id(spec, modality, ids),
            "region-type" => list_files_by_region_type(spec, modality, ids),
            _ => HashMap::new(),
        }
    };

    match ids {
        None => list_files(&selector),
        Some(v) if v.is_empty() => list_files(&selector),
        Some(v) => list_files_by_id(&selector, v),
    }
}

fn list_read_files(spec: &Assay, modality: &String) -> HashMap<String, Vec<File>> {
    let mut files: HashMap<String, Vec<File>> = HashMap::new();
    for rd in spec.get_seqspec(modality) {
        if !rd.files.is_empty() {
            files.insert(rd.read_id, rd.files);
        }
    }
    files
}

fn list_all_files(spec: &Assay, modality: &String) -> HashMap<String, Vec<File>> {
    let mut rd = list_read_files(spec, modality);
    let rgn = list_region_files(spec, modality);
    rd.extend(rgn);
    rd
}

fn list_onlist_files(spec: &Assay, modality: &String) -> HashMap<String, Vec<Onlist>> {
    let mut files: HashMap<String, Vec<Onlist>> = HashMap::new();
    let regions = spec.get_libspec(modality).unwrap().get_onlist_regions();
    for r in regions {
        if let Some(ol) = r.onlist {
            files.entry(r.region_id).or_default().push(ol);
        }
    }
    files
}

fn list_region_files(spec: &Assay, modality: &String) -> HashMap<String, Vec<File>> {
    // convert Onlist to File-shaped map by copying fields
    let onlists = list_onlist_files(spec, modality);
    let mut files: HashMap<String, Vec<File>> = HashMap::new();
    for (region_id, v) in onlists {
        let mut out: Vec<File> = Vec::new();
        for ol in v {
            out.push(File {
                file_id: ol.file_id,
                filename: ol.filename,
                filetype: ol.filetype,
                filesize: ol.filesize,
                url: ol.url,
                urltype: ol.urltype,
                md5: ol.md5,
            });
        }
        files.insert(region_id, out);
    }
    files
}

fn format_list_files_metadata(
    files: &HashMap<String, Vec<File>>,
    k: &String,
    _spec_base: Option<&Path>,
    _fp: bool,
) -> String {
    let mut x: Vec<String> = Vec::new();
    for row in iter_file_rows(files) {
        if k == "all" {
            for (key, item) in row {
                x.push(format!(
                    "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
                    key,
                    item.file_id,
                    item.filename,
                    item.filetype,
                    item.filesize,
                    item.url,
                    item.urltype,
                    item.md5
                ));
            }
        } else {
            for (key, item) in row {
                let attr = match k.as_str() {
                    "url" => item.url.clone(),
                    "file_id" => item.file_id.clone(),
                    "filename" => item.filename.clone(),
                    "filetype" => item.filetype.clone(),
                    "filesize" => item.filesize.to_string(),
                    "urltype" => item.urltype.clone(),
                    "md5" => item.md5.clone(),
                    _ => String::new(),
                };
                x.push(format!("{}\t{}\t{}", key, item.file_id, attr));
            }
        }
    }
    x.join("\n")
}

fn format_json_files(
    files: &HashMap<String, Vec<File>>,
    k: &String,
    spec_base: Option<&Path>,
    fp: bool,
) -> String {
    use serde_json::json;
    let mut x: Vec<serde_json::Value> = Vec::new();
    for row in iter_file_rows(files) {
        for (_key, item) in row {
            if k == "all" {
                let mut d = serde_json::to_value(item).unwrap();
                if item.urltype == "local" && fp {
                    if let Some(obj) = d.as_object_mut() {
                        obj.insert("url".to_string(), json!(full_path(spec_base, &item.url)));
                    }
                }
                x.push(d);
            } else {
                let mut attr = match k.as_str() {
                    "url" => maybe_full(&item.url, &item.urltype, spec_base, fp),
                    _ => String::new(),
                };
                if k != "url" {
                    attr = match k.as_str() {
                        "file_id" => item.file_id.clone(),
                        "filename" => item.filename.clone(),
                        "filetype" => item.filetype.clone(),
                        "filesize" => item.filesize.to_string(),
                        "urltype" => item.urltype.clone(),
                        "md5" => item.md5.clone(),
                        _ => String::new(),
                    };
                }
                x.push(json!({ "file_id": item.file_id, k: attr }));
            }
        }
    }
    serde_json::to_string_pretty(&x).unwrap()
}

fn format_list_files(
    files: &HashMap<String, Vec<File>>,
    fmt: &String,
    k: Option<&String>,
    spec_base: Option<&Path>,
    fp: bool,
) -> String {
    let mut out: Vec<String> = Vec::new();
    if fmt == "paired" {
        for row in iter_file_rows(files) {
            let mut t: Vec<String> = Vec::new();
            for (_key, i) in row {
                let val = if let Some(key) = k {
                    let mut attr = match key.as_str() {
                        "url" => maybe_full(&i.url, &i.urltype, spec_base, fp),
                        _ => String::new(),
                    };
                    if key != &"url".to_string() {
                        attr = match key.as_str() {
                            "file_id" => i.file_id.clone(),
                            "filename" => i.filename.clone(),
                            "filetype" => i.filetype.clone(),
                            "filesize" => i.filesize.to_string(),
                            "urltype" => i.urltype.clone(),
                            "md5" => i.md5.clone(),
                            _ => String::new(),
                        };
                    }
                    attr
                } else {
                    i.filename.clone()
                };
                t.push(val);
            }
            out.push(t.join("\t"));
        }
    } else if fmt == "interleaved" || fmt == "list" {
        for row in iter_file_rows(files) {
            for (_key, i) in row {
                let id = if let Some(key) = k {
                    let mut attr = match key.as_str() {
                        "url" => maybe_full(&i.url, &i.urltype, spec_base, fp),
                        _ => String::new(),
                    };
                    if key != &"url".to_string() {
                        attr = match key.as_str() {
                            "file_id" => i.file_id.clone(),
                            "filename" => i.filename.clone(),
                            "filetype" => i.filetype.clone(),
                            "filesize" => i.filesize.to_string(),
                            "urltype" => i.urltype.clone(),
                            "md5" => i.md5.clone(),
                            _ => String::new(),
                        };
                    }
                    attr
                } else {
                    i.filename.clone()
                };
                out.push(id);
            }
        }
    } else if fmt == "index" {
        let mut t: Vec<String> = Vec::new();
        for row in iter_file_rows(files) {
            for (_key, i) in row {
                let id = if let Some(key) = k {
                    let mut attr = match key.as_str() {
                        "url" => maybe_full(&i.url, &i.urltype, spec_base, fp),
                        _ => String::new(),
                    };
                    if key != &"url".to_string() {
                        attr = match key.as_str() {
                            "file_id" => i.file_id.clone(),
                            "filename" => i.filename.clone(),
                            "filetype" => i.filetype.clone(),
                            "filesize" => i.filesize.to_string(),
                            "urltype" => i.urltype.clone(),
                            "md5" => i.md5.clone(),
                            _ => String::new(),
                        };
                    }
                    attr
                } else {
                    i.filename.clone()
                };
                t.push(id);
            }
        }
        out.push(t.join(","));
    }
    out.join("\n")
}

fn ordered_file_columns<'a>(
    files: &'a HashMap<String, Vec<File>>,
) -> Vec<(&'a String, &'a Vec<File>)> {
    let mut columns: Vec<(&String, &Vec<File>)> = files.iter().collect();
    columns.sort_by(|(left, _), (right, _)| left.cmp(right));
    columns
}

fn iter_file_rows<'a>(files: &'a HashMap<String, Vec<File>>) -> Vec<Vec<(&'a String, &'a File)>> {
    let columns = ordered_file_columns(files);
    let row_count = columns
        .iter()
        .map(|(_, items)| items.len())
        .min()
        .unwrap_or(0);
    let mut rows = Vec::new();
    for row_idx in 0..row_count {
        let mut row = Vec::new();
        for (key, items) in &columns {
            row.push((*key, &items[row_idx]));
        }
        rows.push(row);
    }
    rows
}

fn list_files_by_read_id(
    spec: &Assay,
    modality: &String,
    read_ids: &Vec<String>,
) -> HashMap<String, Vec<File>> {
    let mut files: HashMap<String, Vec<File>> = HashMap::new();
    let ids: HashSet<String> = read_ids.iter().cloned().collect();
    for read in spec.get_seqspec(modality) {
        if ids.contains(&read.read_id) && !read.files.is_empty() {
            files.entry(read.read_id).or_default().extend(read.files);
        }
    }
    files
}

fn list_files_by_file_id(
    spec: &Assay,
    modality: &String,
    file_ids: &Vec<String>,
) -> HashMap<String, Vec<File>> {
    let mut files: HashMap<String, Vec<File>> = HashMap::new();
    let ids: HashSet<String> = file_ids.iter().cloned().collect();
    for read in spec.get_seqspec(modality) {
        for file in read.files {
            if ids.contains(&file.filename) {
                files.entry(read.read_id.clone()).or_default().push(file);
            }
        }
    }
    files
}

fn list_files_by_region_id(
    spec: &Assay,
    modality: &String,
    region_ids: &Vec<String>,
) -> HashMap<String, Vec<File>> {
    let files = list_region_files(spec, modality);
    let ids: HashSet<String> = region_ids.iter().cloned().collect();
    let mut new_files: HashMap<String, Vec<File>> = HashMap::new();
    for (region_id, region_files) in files {
        if ids.contains(&region_id) {
            new_files.entry(region_id).or_default().extend(region_files);
        }
    }
    new_files
}

fn list_files_by_region_type(
    spec: &Assay,
    modality: &String,
    region_types: &Vec<String>,
) -> HashMap<String, Vec<File>> {
    let files = list_region_files(spec, modality);
    let ids: HashSet<String> = region_types.iter().cloned().collect();
    let mut new_files: HashMap<String, Vec<File>> = HashMap::new();
    for (region_id, region_files) in files {
        let m = spec.get_libspec(modality).unwrap();
        let regions = m.get_region_by_id(&region_id);
        let r = regions.first().unwrap().clone();
        if ids.contains(&r.region_type) {
            new_files.entry(region_id).or_default().extend(region_files);
        }
    }
    new_files
}

fn maybe_full(url: &String, urltype: &String, spec_base: Option<&Path>, fp: bool) -> String {
    if urltype == "local" && fp {
        full_path(spec_base, url)
    } else {
        url.clone()
    }
}

fn full_path(spec_base: Option<&Path>, url: &String) -> String {
    spec_base
        .map(|base| base.join(url).to_string_lossy().to_string())
        .unwrap_or_else(|| url.clone())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_seqspec_file_read_selector() {
        let spec = dogma_spec();
        let files = seqspec_file(&spec, &"rna".into(), None, &"read".into());
        assert!(!files.is_empty());
        // Each key should be a read_id
        for (read_id, file_list) in &files {
            assert!(!read_id.is_empty());
            assert!(!file_list.is_empty());
        }
    }

    #[test]
    fn test_seqspec_file_region_selector() {
        let spec = dogma_spec();
        let files = seqspec_file(&spec, &"rna".into(), None, &"region".into());
        // Region files come from onlists, which the rna modality should have
        assert!(!files.is_empty());
    }

    #[test]
    fn test_seqspec_file_all_selector() {
        let spec = dogma_spec();
        let all_files = seqspec_file(&spec, &"rna".into(), None, &"file".into());
        let read_files = seqspec_file(&spec, &"rna".into(), None, &"read".into());
        let region_files = seqspec_file(&spec, &"rna".into(), None, &"region".into());
        // "file" selector returns union of read and region files
        assert!(all_files.len() >= read_files.len());
        assert!(all_files.len() >= region_files.len());
    }

    #[test]
    fn test_seqspec_file_by_read_id() {
        let spec = dogma_spec();
        let rna_reads = spec.get_seqspec("rna");
        let read_id = rna_reads[0].read_id.clone();
        let ids = vec![read_id.clone()];
        let files = seqspec_file(&spec, &"rna".into(), Some(&ids), &"read".into());
        assert!(files.contains_key(&read_id));
    }

    #[test]
    fn test_full_path() {
        let spec_fn = PathBuf::from("/data/specs/spec.yaml");
        let url = "barcodes.txt".to_string();
        let result = full_path(spec_fn.parent(), &url);
        assert_eq!(result, "/data/specs/barcodes.txt");
    }

    #[test]
    fn test_maybe_full_local() {
        let spec_fn = PathBuf::from("/data/specs/spec.yaml");
        let url = "file.txt".to_string();
        let result = maybe_full(&url, &"local".to_string(), spec_fn.parent(), true);
        assert_eq!(result, "/data/specs/file.txt");
    }

    #[test]
    fn test_maybe_full_remote() {
        let spec_fn = PathBuf::from("/data/specs/spec.yaml");
        let url = "http://example.com/file.txt".to_string();
        let result = maybe_full(&url, &"http".to_string(), spec_fn.parent(), true);
        assert_eq!(result, "http://example.com/file.txt");
    }

    #[test]
    fn test_format_list_files_paired_uses_row_major_order() {
        let mut files = HashMap::new();
        files.insert(
            "rna_R1".to_string(),
            vec![
                File::new(
                    "r1_a".into(),
                    "r1_a.fastq.gz".into(),
                    "fastq".into(),
                    0,
                    "r1_a.fastq.gz".into(),
                    "local".into(),
                    "".into(),
                ),
                File::new(
                    "r1_b".into(),
                    "r1_b.fastq.gz".into(),
                    "fastq".into(),
                    0,
                    "r1_b.fastq.gz".into(),
                    "local".into(),
                    "".into(),
                ),
            ],
        );
        files.insert(
            "rna_R2".to_string(),
            vec![
                File::new(
                    "r2_a".into(),
                    "r2_a.fastq.gz".into(),
                    "fastq".into(),
                    0,
                    "r2_a.fastq.gz".into(),
                    "local".into(),
                    "".into(),
                ),
                File::new(
                    "r2_b".into(),
                    "r2_b.fastq.gz".into(),
                    "fastq".into(),
                    0,
                    "r2_b.fastq.gz".into(),
                    "local".into(),
                    "".into(),
                ),
            ],
        );

        let rendered = format_list_files(
            &files,
            &"paired".to_string(),
            Some(&"filename".to_string()),
            Some(Path::new(".")),
            false,
        );
        assert_eq!(
            rendered,
            "r1_a.fastq.gz\tr2_a.fastq.gz\nr1_b.fastq.gz\tr2_b.fastq.gz"
        );
    }

    #[test]
    fn test_format_list_files_metadata_keeps_raw_local_url() {
        let mut files = HashMap::new();
        files.insert(
            "rna_R1".to_string(),
            vec![File::new(
                "r1".into(),
                "r1.fastq.gz".into(),
                "fastq".into(),
                0,
                "relative/r1.fastq.gz".into(),
                "local".into(),
                "".into(),
            )],
        );

        let rendered = format_list_files_metadata(
            &files,
            &"url".to_string(),
            Some(Path::new("/tmp")),
            true,
        );
        assert_eq!(rendered, "rna_R1\tr1\trelative/r1.fastq.gz");
    }
}
