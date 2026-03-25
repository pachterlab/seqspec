use crate::auth::RemoteAccess;
use crate::models::assay::Assay;
use crate::models::onlist::Onlist;
use crate::seqspec_find::{find_by_region_id, find_by_region_type};
use crate::utils;
use clap::Args;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Debug, Args)]
pub struct OnlistArgs {
    #[clap(
        short,
        long,
        help = "Path to output file (required for download/join operations)",
        value_name = "OUT"
    )]
    output: Option<PathBuf>,

    #[clap(short, long, help = "Selector", value_parser = ["read", "region", "region-type"], default_value = "read")]
    selector: String,

    #[clap(short, long, help = "Format for combining multiple onlists", value_parser = ["product", "multi"], default_value = None)]
    format: Option<String>,

    #[clap(short = 'i', long, help = "ID to search for")]
    id: Option<String>,

    #[clap(short, long, help = "Modality", required = true)]
    modality: String,

    #[clap(long, env = "SEQSPEC_AUTH_PROFILE", value_name = "PROFILE")]
    auth_profile: Option<String>,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,
}

pub fn run_onlist(args: &OnlistArgs) {
    validate_onlist_args(args);
    let base_path = args
        .yaml
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .to_path_buf();
    let spec = utils::load_spec(&args.yaml);
    let remote_access = RemoteAccess::load(args.auth_profile.as_deref()).unwrap_or_else(|err| {
        eprintln!("{}", err);
        std::process::exit(1);
    });

    let onlists = get_onlists(&spec, &args.modality, &args.selector, args.id.as_deref())
        .unwrap_or_else(|err| {
            eprintln!("{}", err);
            std::process::exit(1);
        });
    if onlists.is_empty() {
        println!("No onlists found");
        return;
    }

    if let Some(fmt) = &args.format {
        let save_path = args.output.clone().unwrap_or(base_path.join("joined.txt"));
        let result_path =
            join_onlists_and_save(&onlists, fmt, &save_path, &base_path, &remote_access);
        println!("{}", result_path.display());
    } else if let Some(out) = &args.output {
        let result_paths = download_onlists_to_path(&onlists, out, &base_path, &remote_access);
        for p in result_paths {
            println!("{}", p.url);
        }
    } else {
        let urls = get_onlist_urls(&onlists, &base_path);
        for u in urls {
            println!("{}", u.url);
        }
    }
}

fn validate_onlist_args(args: &OnlistArgs) {
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

fn get_onlists(
    spec: &Assay,
    modality: &str,
    selector: &str,
    id: Option<&str>,
) -> Result<Vec<Onlist>, String> {
    match selector {
        "region-type" => {
            let mut out: Vec<Onlist> = Vec::new();
            let mut matches_by_read: Vec<(String, Vec<Onlist>)> = Vec::new();
            for rd in spec.get_seqspec(modality) {
                if let Ok((_read, rgns)) =
                    utils::map_read_id_to_regions(spec, modality, &rd.read_id)
                {
                    let mut ordered: Vec<Onlist> = Vec::new();
                    for r in rgns {
                        if r.region_type == id.unwrap_or("") {
                            if let Some(ol) = r.get_onlist() {
                                ordered.push(ol);
                            }
                        }
                    }
                    if !ordered.is_empty() {
                        matches_by_read.push((rd.read_id.clone(), ordered));
                    }
                }
            }
            if matches_by_read.len() == 1 {
                return Ok(matches_by_read.remove(0).1);
            }
            if matches_by_read.len() > 1 {
                let read_ids = matches_by_read
                    .iter()
                    .map(|(read_id, _)| read_id.as_str())
                    .collect::<Vec<_>>()
                    .join(", ");
                return Err(format!(
                    "region-type '{}' matches regions in multiple reads for modality '{}': {}. Use -s read or -s region to disambiguate.",
                    id.unwrap_or(""),
                    modality,
                    read_ids
                ));
            }
            let regions = find_by_region_type(spec, modality, id.unwrap_or(""));
            for r in regions {
                if let Some(ol) = r.get_onlist() {
                    out.push(ol);
                }
            }
            Ok(out)
        }
        "region" => {
            let mut out: Vec<Onlist> = Vec::new();
            let regions = find_by_region_id(spec, modality, id.unwrap_or(""));
            for r in regions {
                if let Some(ol) = r.get_onlist() {
                    out.push(ol);
                }
            }
            if out.is_empty() {
                return Err(format!("No onlist found for region {}", id.unwrap_or("")));
            }
            Ok(out)
        }
        "read" => {
            let (read, rgns) = utils::map_read_id_to_regions(spec, modality, id.unwrap_or(""))
                .map_err(|err| err.to_string())?;
            let region_coordinates = utils::project_regions_to_coordinates(rgns);
            let clipped = utils::itx_read(region_coordinates, 0, read.max_len);
            let mut out: Vec<Onlist> = Vec::new();
            for rc in clipped {
                if let Some(ol) = rc.region.get_onlist() {
                    out.push(ol);
                }
            }
            Ok(out)
        }
        _ => Ok(Vec::new()),
    }
}

struct UrlInfo {
    url: String,
}

fn get_onlist_urls(onlists: &Vec<Onlist>, base_path: &Path) -> Vec<UrlInfo> {
    let mut urls = Vec::new();
    for ol in onlists {
        let url = if ol.urltype == "local" {
            base_path
                .join(utils::local_onlist_locator(ol).unwrap_or_else(|err| {
                    eprintln!("{}", err);
                    std::process::exit(1);
                }))
                .to_string_lossy()
                .to_string()
        } else {
            ol.url.clone()
        };
        urls.push(UrlInfo { url });
    }
    urls
}

struct PathInfo {
    url: String,
}

fn download_onlists_to_path(
    onlists: &Vec<Onlist>,
    output_path: &Path,
    base_path: &Path,
    remote_access: &RemoteAccess,
) -> Vec<PathInfo> {
    let mut out = Vec::new();
    for ol in onlists {
        if ol.urltype == "local" {
            let local = base_path.join(utils::local_onlist_locator(ol).unwrap_or_else(|err| {
                eprintln!("{}", err);
                std::process::exit(1);
            }));
            out.push(PathInfo {
                url: local.to_string_lossy().to_string(),
            });
        } else {
            let content = utils::read_remote_list(&ol.url, remote_access).unwrap_or_default();
            let filename = format!(
                "{}_{}",
                ol.file_id,
                output_path
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
            );
            let download_path = output_path
                .parent()
                .unwrap_or_else(|| Path::new("."))
                .join(filename);
            write_onlist(&content, &download_path);
            out.push(PathInfo {
                url: download_path.to_string_lossy().to_string(),
            });
        }
    }
    out
}

fn join_onlists_and_save(
    onlists: &Vec<Onlist>,
    format_type: &str,
    output_path: &Path,
    base_path: &Path,
    remote_access: &RemoteAccess,
) -> PathBuf {
    let mut contents: Vec<Vec<String>> = Vec::new();
    for ol in onlists {
        let content = if ol.urltype == "local" {
            let locator = utils::local_onlist_locator(ol).unwrap_or_else(|err| {
                eprintln!("{}", err);
                std::process::exit(1);
            });
            utils::read_local_list(&base_path.join(locator)).unwrap_or_default()
        } else {
            utils::read_remote_list(&ol.url, remote_access).unwrap_or_default()
        };
        contents.push(content);
    }
    let joined = join_onlist_contents(contents, format_type);
    write_onlist(&joined, output_path);
    output_path.to_path_buf()
}

fn write_onlist(onlist: &Vec<String>, path: &Path) {
    let mut f = fs::File::create(path).unwrap();
    for line in onlist {
        writeln!(f, "{}", line).unwrap();
    }
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
        if rest.is_empty() {
            return acc;
        }
        let mut out = Vec::new();
        for a in &acc {
            for b in &rest[0] {
                out.push(format!("{}{}", a, b));
            }
        }
        cartesian(out, &rest[1..])
    }
    if lsts.is_empty() {
        return Vec::new();
    }
    let init = lsts[0].clone();
    cartesian(init, &lsts[1..])
}

fn join_multi_onlist(lsts: Vec<Vec<String>>) -> Vec<String> {
    let max_len = lsts.iter().map(|v| v.len()).max().unwrap_or(0);
    let mut out = Vec::new();
    for i in 0..max_len {
        let row: Vec<String> = lsts
            .iter()
            .map(|v| v.get(i).cloned().unwrap_or_else(|| "-".to_string()))
            .collect();
        out.push(row.join(" "));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn unique_test_dir(prefix: &str) -> PathBuf {
        std::env::temp_dir().join(format!(
            "{}-{}-{}",
            prefix,
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ))
    }

    #[test]
    fn test_join_product() {
        let lists = vec![vec!["A".into(), "B".into()], vec!["1".into(), "2".into()]];
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
        let lists = vec![vec!["A".into(), "B".into()], vec!["1".into(), "2".into()]];
        let product = join_onlist_contents(lists.clone(), "product");
        assert_eq!(product.len(), 4);

        let multi = join_onlist_contents(lists, "multi");
        assert_eq!(multi.len(), 2);

        let unknown = join_onlist_contents(vec![], "invalid");
        assert!(unknown.is_empty());
    }

    #[test]
    fn test_get_onlists_by_region_type_errors_when_matches_span_reads() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let err = get_onlists(&spec, "rna", "region-type", Some("barcode")).unwrap_err();
        assert!(err.contains("matches regions in multiple reads"));
        assert!(err.contains("rna_R1"));
        assert!(err.contains("rna_R2"));
    }

    #[test]
    fn test_get_onlists_by_region() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let onlists = get_onlists(&spec, "rna", "region", Some("rna_cell_bc")).unwrap();
        assert_eq!(onlists.len(), 1);
        assert_eq!(onlists[0].filename, "RNA-737K-arc-v1.txt");
    }

    #[test]
    fn test_get_onlists_by_read() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let rna_reads = spec.get_seqspec("rna");
        assert_eq!(rna_reads.len(), 2);
        // rna_R1 maps to regions including rna_cell_bc which has an onlist
        let onlists = get_onlists(&spec, "rna", "read", Some(&rna_reads[0].read_id)).unwrap();
        assert_eq!(onlists.len(), 1);
        assert_eq!(onlists[0].filename, "RNA-737K-arc-v1.txt");
    }

    #[test]
    fn test_get_onlists_by_read_respects_read_window() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from(
            "tests/fixtures/onlist_read_clip/spec.yaml",
        ));
        let onlists = get_onlists(&spec, "rna", "read", Some("rna_read")).unwrap();
        let file_ids = onlists
            .iter()
            .map(|onlist| onlist.file_id.as_str())
            .collect::<Vec<_>>();
        assert_eq!(file_ids, vec!["barcode_a.txt"]);
    }

    #[test]
    fn test_get_onlists_empty_modality() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let onlists = get_onlists(&spec, "rna", "region-type", Some("nonexistent_type")).unwrap();
        assert!(onlists.is_empty());
    }

    #[test]
    fn test_get_onlists_region_type_uses_read_order_when_unique() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from(
            "tests/fixtures/onlist_issue_68/spec.yaml",
        ));
        let onlists = get_onlists(&spec, "rna", "region-type", Some("barcode")).unwrap();
        let file_ids = onlists
            .iter()
            .map(|onlist| onlist.file_id.as_str())
            .collect::<Vec<_>>();
        assert_eq!(file_ids, vec!["barcode_b.txt", "barcode_a.txt"]);
    }

    #[test]
    fn test_get_onlists_region_type_errors_when_matches_span_multiple_reads() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from(
            "tests/fixtures/onlist_ambiguous_region_type/spec.yaml",
        ));
        let err = get_onlists(&spec, "rna", "region-type", Some("barcode")).unwrap_err();
        assert!(err.contains("matches regions in multiple reads"));
        assert!(err.contains("rna_read_1"));
        assert!(err.contains("rna_read_2"));
    }

    #[test]
    fn test_get_onlist_urls_prefers_local_url() {
        let base = PathBuf::from("/tmp/spec-root");
        let onlists = vec![Onlist::new(
            "ol1".into(),
            "display.txt".into(),
            "txt".into(),
            0,
            "nested/whitelist.txt".into(),
            "local".into(),
            String::new(),
        )];

        let urls = get_onlist_urls(&onlists, &base);
        assert_eq!(urls[0].url, "/tmp/spec-root/nested/whitelist.txt");
    }

    #[test]
    fn test_join_onlists_and_save_reads_local_onlists_from_url() {
        let root = unique_test_dir("seqspec-onlist");
        let nested = root.join("nested");
        std::fs::create_dir_all(&nested).unwrap();
        std::fs::write(nested.join("whitelist.txt"), "AAAA\nCCCC\n").unwrap();

        let onlists = vec![Onlist::new(
            "ol1".into(),
            "display.txt".into(),
            "txt".into(),
            0,
            "nested/whitelist.txt".into(),
            "local".into(),
            String::new(),
        )];
        let output = root.join("joined.txt");
        let remote_access = RemoteAccess::anonymous();

        let result_path =
            join_onlists_and_save(&onlists, "product", &output, &root, &remote_access);

        assert_eq!(result_path, output);
        assert_eq!(std::fs::read_to_string(&output).unwrap(), "AAAA\nCCCC\n");

        std::fs::remove_dir_all(root).unwrap();
    }
}
