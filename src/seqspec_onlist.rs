use crate::models::assay::Assay;
use crate::models::read::Read;
use crate::models::onlist::Onlist;
use crate::seqspec_find::{find_by_region_id, find_by_region_type};
use crate::utils;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Debug, Args)]
pub struct OnlistArgs {
    #[clap(short, long, help = "Path to output file (required for download/join operations)", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(short, long, help = "Selector", value_parser = ["read", "region", "region-type"], default_value = "read")]
    selector: String,

    #[clap(short, long, help = "Format for combining multiple onlists", value_parser = ["product", "multi"], default_value = None)]
    format: Option<String>,

    #[clap(short = 'i', long, help = "ID to search for")]
    id: Option<String>,

    #[clap(short, long, help = "Modality", required = true)]
    modality: String,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,
}

pub fn run_onlist(args: &OnlistArgs) {
    validate_onlist_args(args);
    let base_path = args.yaml.parent().unwrap_or_else(|| Path::new(".")).to_path_buf();
    let spec = utils::load_spec(&args.yaml);

    let onlists = get_onlists(&spec, &args.modality, &args.selector, args.id.as_deref());
    if onlists.is_empty() { println!("No onlists found"); return; }

    if let Some(fmt) = &args.format {
        let save_path = args.output.clone().unwrap_or(base_path.join("joined.txt"));
        let result_path = join_onlists_and_save(&onlists, fmt, &save_path, &base_path);
        println!("{}", result_path.display());
    } else if let Some(out) = &args.output {
        let result_paths = download_onlists_to_path(&onlists, out, &base_path);
        for p in result_paths { println!("{}", p.url); }
    } else {
        let urls = get_onlist_urls(&onlists, &base_path);
        for u in urls { println!("{}", u.url); }
    }
}

fn validate_onlist_args(args: &OnlistArgs) {
    if !args.yaml.exists() { eprintln!("Input file does not exist: {}", args.yaml.display()); std::process::exit(1); }
    if let Some(out) = &args.output { if out.exists() && !out.is_file() { eprintln!("Output path exists but is not a file: {}", out.display()); std::process::exit(1); } }
}

fn get_onlists(spec: &Assay, modality: &str, selector: &str, id: Option<&str>) -> Vec<Onlist> {
    match selector {
        "region-type" => {
            let mut out: Vec<Onlist> = Vec::new();
            for rd in spec.get_seqspec(modality) {
                if let Ok((_read, rgns)) = utils::map_read_id_to_regions(spec, modality, &rd.read_id) {
                    let mut ordered: Vec<Onlist> = Vec::new();
                    for r in rgns { if r.region_type == id.unwrap_or("") { if let Some(ol) = r.get_onlist() { ordered.push(ol); } } }
                    if !ordered.is_empty() { return ordered; }
                }
            }
            let regions = find_by_region_type(spec, modality, id.unwrap_or(""));
            for r in regions { if let Some(ol) = r.get_onlist() { out.push(ol); } }
            out
        }
        "region" => {
            let mut out: Vec<Onlist> = Vec::new();
            let regions = find_by_region_id(spec, modality, id.unwrap_or(""));
            for r in regions { if let Some(ol) = r.get_onlist() { out.push(ol); } }
            out
        }
        "read" => {
            let (_read, rgns) = utils::map_read_id_to_regions(spec, modality, id.unwrap_or("")) .unwrap_or_else(|_| (Read{ read_id: String::new(), name: String::new(), modality: String::new(), primer_id: String::new(), min_len:0, max_len:0, strand: "pos".to_string(), files: vec![] }, vec![]));
            let mut out: Vec<Onlist> = Vec::new();
            for r in rgns { if let Some(ol) = r.get_onlist() { out.push(ol); } }
            out
        }
        _ => Vec::new(),
    }
}

struct UrlInfo { url: String }

fn get_onlist_urls(onlists: &Vec<Onlist>, base_path: &Path) -> Vec<UrlInfo> {
    let mut urls = Vec::new();
    for ol in onlists {
        let url = if ol.urltype == "local" { base_path.join(&ol.url).to_string_lossy().to_string() } else { ol.url.clone() };
        urls.push(UrlInfo { url });
    }
    urls
}

struct PathInfo { url: String }

fn download_onlists_to_path(onlists: &Vec<Onlist>, output_path: &Path, base_path: &Path) -> Vec<PathInfo> {
    let mut out = Vec::new();
    for ol in onlists {
        if ol.urltype == "local" {
            let local = base_path.join(&ol.url);
            out.push(PathInfo { url: local.to_string_lossy().to_string() });
        } else {
            let content = utils::read_remote_list(&ol.url).unwrap_or_default();
            let filename = format!("{}_{}", ol.file_id, output_path.file_name().unwrap_or_default().to_string_lossy());
            let download_path = output_path.parent().unwrap_or_else(|| Path::new(".")).join(filename);
            write_onlist(&content, &download_path);
            out.push(PathInfo { url: download_path.to_string_lossy().to_string() });
        }
    }
    out
}

fn join_onlists_and_save(onlists: &Vec<Onlist>, format_type: &str, output_path: &Path, base_path: &Path) -> PathBuf {
    let mut contents: Vec<Vec<String>> = Vec::new();
    for ol in onlists {
        let content = if ol.urltype == "local" { utils::read_local_list(&base_path.join(&ol.url)).unwrap_or_default() } else { utils::read_remote_list(&ol.url).unwrap_or_default() };
        contents.push(content);
    }
    let joined = join_onlist_contents(contents, format_type);
    write_onlist(&joined, output_path);
    output_path.to_path_buf()
}

fn write_onlist(onlist: &Vec<String>, path: &Path) {
    let mut f = fs::File::create(path).unwrap();
    for line in onlist { writeln!(f, "{}", line).unwrap(); }
}

fn join_onlist_contents(lists: Vec<Vec<String>>, format_type: &str) -> Vec<String> {
    match format_type {
        "product" => join_product_onlist(lists),
        "multi" => join_multi_onlist(lists),
        _ => Vec::new(),
    }
}

fn join_product_onlist(lsts: Vec<Vec<String>>) -> Vec<String> {
    fn cartesian(acc: Vec<String>, rest: &[Vec<String>]) -> Vec<String> {
        if rest.is_empty() { return acc; }
        let mut out = Vec::new();
        for a in &acc { for b in &rest[0] { out.push(format!("{}{}", a, b)); } }
        cartesian(out, &rest[1..])
    }
    if lsts.is_empty() { return Vec::new(); }
    let init = lsts[0].clone();
    cartesian(init, &lsts[1..])
}

fn join_multi_onlist(lsts: Vec<Vec<String>>) -> Vec<String> {
    let max_len = lsts.iter().map(|v| v.len()).max().unwrap_or(0);
    let mut out = Vec::new();
    for i in 0..max_len {
        let row: Vec<String> = lsts.iter().map(|v| v.get(i).cloned().unwrap_or_else(|| "-".to_string())).collect();
        out.push(row.join(" "));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_join_product() {
        let lists = vec![
            vec!["A".into(), "B".into()],
            vec!["1".into(), "2".into()],
        ];
        let result = join_product_onlist(lists);
        assert_eq!(result.len(), 4);
        assert!(result.contains(&"A1".to_string()));
        assert!(result.contains(&"A2".to_string()));
        assert!(result.contains(&"B1".to_string()));
        assert!(result.contains(&"B2".to_string()));
    }

    #[test]
    fn test_join_product_three_lists() {
        let lists = vec![
            vec!["A".into(), "B".into()],
            vec!["1".into()],
            vec!["x".into(), "y".into()],
        ];
        let result = join_product_onlist(lists);
        assert_eq!(result.len(), 4); // 2 * 1 * 2
        assert!(result.contains(&"A1x".to_string()));
        assert!(result.contains(&"B1y".to_string()));
    }

    #[test]
    fn test_join_product_empty() {
        let lists: Vec<Vec<String>> = vec![];
        let result = join_product_onlist(lists);
        assert!(result.is_empty());
    }

    #[test]
    fn test_join_multi() {
        let lists = vec![
            vec!["A".into(), "B".into(), "C".into()],
            vec!["1".into(), "2".into()],
        ];
        let result = join_multi_onlist(lists);
        assert_eq!(result.len(), 3); // max length
        assert_eq!(result[0], "A 1");
        assert_eq!(result[1], "B 2");
        assert_eq!(result[2], "C -"); // padded with "-"
    }

    #[test]
    fn test_join_multi_empty() {
        let lists: Vec<Vec<String>> = vec![];
        let result = join_multi_onlist(lists);
        assert!(result.is_empty());
    }

    #[test]
    fn test_join_onlist_contents_dispatches() {
        let lists = vec![
            vec!["A".into(), "B".into()],
            vec!["1".into(), "2".into()],
        ];
        let product = join_onlist_contents(lists.clone(), "product");
        assert_eq!(product.len(), 4);

        let multi = join_onlist_contents(lists, "multi");
        assert_eq!(multi.len(), 2);

        let unknown = join_onlist_contents(vec![], "invalid");
        assert!(unknown.is_empty());
    }

    #[test]
    fn test_get_onlists_by_region_type() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let onlists = get_onlists(&spec, "rna", "region-type", Some("barcode"));
        // RNA modality should have barcode regions with onlists
        assert!(!onlists.is_empty());
    }

    #[test]
    fn test_get_onlists_by_region() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        // Find a region that has an onlist
        let lib = spec.get_libspec("rna").unwrap();
        let onlist_regions = lib.get_onlist_regions();
        if let Some(r) = onlist_regions.first() {
            let onlists = get_onlists(&spec, "rna", "region", Some(&r.region_id));
            assert!(!onlists.is_empty());
        }
    }

    #[test]
    fn test_get_onlists_by_read() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let rna_reads = spec.get_seqspec("rna");
        if !rna_reads.is_empty() {
            let onlists = get_onlists(&spec, "rna", "read", Some(&rna_reads[0].read_id));
            // May or may not have onlists depending on read
            // Just verify it doesn't panic
            let _ = onlists;
        }
    }

    #[test]
    fn test_get_onlists_empty_modality() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let onlists = get_onlists(&spec, "rna", "region-type", Some("nonexistent_type"));
        assert!(onlists.is_empty());
    }
}
