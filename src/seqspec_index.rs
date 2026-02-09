use crate::utils;
use std::path::PathBuf;
use std::fs;
use std::io::Write;
// use std::str::FromStr;

use clap::Args;
use crate::models::assay::Assay;
use crate::models::coordinate::Coordinate;
use crate::models::file::File;
use crate::models::region::{Region, RegionCoordinate, RegionCoordinateDifference};
use crate::seqspec_find::find_by_region_id;
use std::collections::{HashMap, HashSet};

#[derive(Debug, Args)]
pub struct IndexArgs {
    #[clap(short, long, help = "Output file path", value_name = "OUT")]
    output: Option<PathBuf>,

    #[clap(help = "Sequencing specification yaml file", required = true)]
    yaml: PathBuf,

    #[clap(
        short,
        long,
        help = "Tool",
        value_name = "TOOL",
        required = true,
        value_parser = ["chromap", "kb", "kb-single", "relative", "seqkit", "simpleaf", "starsolo", "splitcode", "tab", "zumis"],
        default_value = "tab",
        required = false
    )]
    tool: String,

    #[clap(
        short,
        long,
        help = "Selector",
        value_name = "SELECTOR",
        value_parser = ["read", "region", "file", "region-type"],
        default_value = "read",
        required = false
    )]
    selector: String,

    #[clap(
        short,
        long,
        help = "Modality",
        value_name = "MODALITY",
        required = true
    )]
    modality: String,

    #[clap(short, long, help = "IDs (comma-separated)", value_name = "IDS", required = false, value_delimiter = ',')]
    ids: Option<Vec<String>>,

    #[clap(short, long, help = "Rev", value_name = "REV", required = false, default_value = "false")]
    rev: bool,

    #[clap(long, help = "Subregion Type", value_name = "SUBREGIONTYPE", required = false)]
    subregion_type: Option<String>,

    #[clap(long, help = "No Overlap", value_name = "NOOVERLAP", required = false, default_value = "false")]
    no_overlap: bool,
}

pub fn validate_index_args(args: &IndexArgs) -> () {
    if !args.yaml.exists() {
        eprintln!("Please use `seqspec index -h` for help.");
        std::process::exit(1);
    }
    if args.modality.is_empty() {
        eprintln!("Please use `seqspec index -h` for help.");
        std::process::exit(1);
    }
    if args.selector.is_empty() {
        eprintln!("Please use `seqspec index -h` for help.");
        std::process::exit(1);
    }
}

pub fn run_index(args: &IndexArgs) {
    validate_index_args(args);
    let spec = utils::load_spec(&args.yaml);

    let ids = args.ids.as_ref().unwrap_or(&Vec::new()).clone();


    let mut index = seqspec_index(&spec, &args.modality, &ids, &args.selector, &args.rev);
    if args.no_overlap {
        index = filter_index_no_overlap(index);
    }
    let fmt = format_index(&index, &args.tool, &args.subregion_type);
    // write to output
    if let Some(output) = &args.output {
        let mut file = fs::File::create(output).unwrap();
        writeln!(file, "{}", fmt).unwrap();
    } else {
        println!("{}", fmt);
    }
}

pub fn seqspec_index(spec: &Assay, modality: &String, ids: &Vec<String>, idtype: &String, _rev: &bool) -> Vec<Coordinate> {
    match (idtype.as_str(), ids.is_empty()) {
        ("file", true) => get_index_by_files(spec, modality),
        ("read", true) => get_index_by_reads(spec, modality),
        ("region", true) => get_index_by_regions(spec, modality),
        ("file", false) => get_index_by_file_ids(spec, modality, ids),
        ("region", false) => get_index_by_region_ids(spec, modality, ids),
        ("read", false) => get_index_by_read_ids(spec, modality, ids),
        _ => Vec::new(),
    }
}

pub fn format_index(index: &Vec<Coordinate>, tool: &String, subregion_type: &Option<String>) -> String {
    match tool.as_str() {
        "chromap" => format_chromap(index),
        "kb" => format_kallisto_bus(index),
        "kb-single" => format_kallisto_bus_force_single(index),
        "relative" => format_relative(index),
        "seqkit" => format_seqkit_subseq(index, subregion_type.as_deref()),
        "simpleaf" => format_simpleaf(index),
        "starsolo" => format_starsolo(index),
        "splitcode" => format_splitcode(index),
        "tab" => format_tab(index),
        "zumis" => format_zumis(index),
        _ => String::new(),
    }
}

// Declarations (implemented below)
fn get_index_by_files(spec: &Assay, modality: &String) -> Vec<Coordinate> {
    let mut all_files: Vec<File> = Vec::new();
    for r in spec.get_seqspec(modality) {
        for f in r.files { all_files.push(f); }
    }
    let file_ids: Vec<String> = all_files.into_iter().map(|f| f.file_id).collect();
    get_index_by_file_ids(spec, modality, &file_ids)
}
fn get_index_by_reads(spec: &Assay, modality: &String) -> Vec<Coordinate> {
    let read_ids: Vec<String> = spec.get_seqspec(modality).into_iter().map(|r| r.read_id).collect();
    get_index_by_read_ids(spec, modality, &read_ids)
}
fn get_index_by_regions(spec: &Assay, modality: &String) -> Vec<Coordinate> {
    let rgn = spec.get_libspec(modality).expect("Modality not found");
    get_index_by_region_ids(spec, modality, &vec![rgn.region_id])
}
fn get_index_by_file_ids(spec: &Assay, modality: &String, file_ids: &Vec<String>) -> Vec<Coordinate> {
    let files_map = list_files_by_file_id(spec, modality, file_ids);
    let mut indices: Vec<Coordinate> = Vec::new();
    for (read_id, files) in files_map {
        let mut coord = get_coordinate_by_read_id(spec, modality, &read_id);
        if let Some(first) = files.first() {
            coord.query_id = first.file_id.clone();
            coord.query_name = first.filename.clone();
            coord.query_type = "File".to_string();
        }
        indices.push(coord);
    }
    indices
}
fn get_index_by_region_ids(spec: &Assay, modality: &String, region_ids: &Vec<String>) -> Vec<Coordinate> {
    let mut indices: Vec<Coordinate> = Vec::new();
    for id in region_ids {
        let coord = get_coordinate_by_region_id(spec, modality, id);
        indices.push(coord);
    }
    indices
}
fn get_index_by_read_ids(spec: &Assay, modality: &String, read_ids: &Vec<String>) -> Vec<Coordinate> {
    let mut indices: Vec<Coordinate> = Vec::new();
    for id in read_ids {
        let coord = get_coordinate_by_read_id(spec, modality, id);
        indices.push(coord);
    }
    indices
}
fn get_coordinate_by_region_id(spec: &Assay, modality: &String, region_id: &str) -> Coordinate {
    let regions = find_by_region_id(spec, modality, region_id);
    let rgn = regions.first().expect("Region not found").clone();
    let leaves: Vec<Region> = rgn.get_leaves();
    let cuts: Vec<RegionCoordinate> = utils::project_regions_to_coordinates(leaves);
    Coordinate {
        query_id: rgn.region_id,
        query_name: rgn.name,
        query_type: "Region".to_string(),
        rcv: cuts,
        strand: "pos".to_string(),
    }
}
fn get_coordinate_by_read_id(spec: &Assay, modality: &String, read_id: &str) -> Coordinate {
    let (read, rgns) = utils::map_read_id_to_regions(spec, modality, read_id).expect("read mapping failed");
    let rcs: Vec<RegionCoordinate> = utils::project_regions_to_coordinates(rgns);
    let new_rcs: Vec<RegionCoordinate> = utils::itx_read(rcs, 0, read.max_len);
    Coordinate {
        query_id: read.read_id,
        query_name: read.name,
        query_type: "Read".to_string(),
        rcv: new_rcs,
        strand: read.strand,
    }
}
fn filter_index_no_overlap(mut indices: Vec<Coordinate>) -> Vec<Coordinate> {
    for idx in &mut indices {
        let mut seen: HashSet<String> = HashSet::new();
        let mut new_rcv: Vec<RegionCoordinate> = Vec::new();
        for rgn in idx.rcv.iter() {
            let rid = rgn.region.region_id.clone();
            if !seen.contains(&rid) {
                new_rcv.push(rgn.clone());
                seen.insert(rid);
            }
        }
        idx.rcv = new_rcv;
    }
    indices
}
fn format_kallisto_bus(indices: &Vec<Coordinate>) -> String {
    let mut bcs: Vec<String> = Vec::new();
    let mut umi: Vec<String> = Vec::new();
    let mut feature: Vec<String> = Vec::new();
    for (idx, obj) in indices.iter().enumerate() {
        for cut in &obj.rcv {
            let rt = cut.region.region_type.to_uppercase();
            if rt == "BARCODE" {
                bcs.push(format!("{},{}{}{}", idx, cut.start, ",", cut.stop));
            } else if rt == "UMI" {
                umi.push(format!("{},{}{}{}", idx, cut.start, ",", cut.stop));
            } else if matches!(rt.as_str(), "CDNA" | "GDNA" | "PROTEIN" | "TAG" | "SGRNA_TARGET") {
                feature.push(format!("{},{}{}{}", idx, cut.start, ",", cut.stop));
            }
        }
    }
    if umi.is_empty() { umi.push("-1,-1,-1".to_string()); }
    if bcs.is_empty() { bcs.push("-1,-1,-1".to_string()); }
    format!("{}:{}:{}", bcs.join(","), umi.join(","), feature.join(","))
}
fn format_kallisto_bus_force_single(indices: &Vec<Coordinate>) -> String {
    let mut bcs: Vec<String> = Vec::new();
    let mut umi: Vec<String> = Vec::new();
    let mut feature: Vec<String> = Vec::new();
    let mut longest_feature: Option<String> = None;
    let mut max_length: i64 = 0;
    for (idx, coord) in indices.iter().enumerate() {
        for cut in &coord.rcv {
            let rt = cut.region.region_type.to_uppercase();
            if rt == "BARCODE" {
                bcs.push(format!("{},{}{}{}", idx, cut.start, ",", cut.stop));
            } else if rt == "UMI" {
                umi.push(format!("{},{}{}{}", idx, cut.start, ",", cut.stop));
            } else if matches!(rt.as_str(), "CDNA" | "GDNA" | "PROTEIN" | "TAG" | "SGRNA_TARGET") {
                let length = cut.stop - cut.start;
                if length > max_length {
                    max_length = length;
                    longest_feature = Some(format!("{},{}{}{}", idx, cut.start, ",", cut.stop));
                }
            }
        }
    }
    if umi.is_empty() { umi.push("-1,-1,-1".to_string()); }
    if bcs.is_empty() { bcs.push("-1,-1,-1".to_string()); }
    if let Some(lf) = longest_feature { feature.push(lf); }
    format!("{}:{}:{}", bcs.join(","), umi.join(","), feature.join(","))
}
fn format_seqkit_subseq(indices: &Vec<Coordinate>, subregion_type: Option<&str>) -> String {
    if indices.is_empty() { return String::new(); }
    let coord = &indices[0];
    let mut x = String::new();
    if let Some(srt) = subregion_type {
        for cut in &coord.rcv {
            if cut.region.region_type == srt {
                x = format!("{}:{}\n", cut.start + 1, cut.stop);
            }
        }
    }
    x
}
fn format_tab(indices: &Vec<Coordinate>) -> String {
    let mut x = String::new();
    for coord in indices {
        for cut in &coord.rcv {
            x.push_str(&format!("{}\t{}\t{}\t{}\t{}\n", coord.query_id, cut.region.name, cut.region.region_type, cut.start, cut.stop));
        }
    }
    if x.ends_with('\n') { x.pop(); }
    x
}
fn format_starsolo(indices: &Vec<Coordinate>) -> String {
    let mut bcs: Vec<String> = Vec::new();
    let mut umi: Vec<String> = Vec::new();
    for coord in indices {
        for cut in &coord.rcv {
            let rt = cut.region.region_type.to_uppercase();
            if rt == "BARCODE" {
                bcs.push(format!("--soloCBstart {} --soloCBlen {}", cut.start + 1, cut.stop - cut.start));
            } else if rt == "UMI" {
                umi.push(format!("--soloUMIstart {} --soloUMIlen {}", cut.start + 1, cut.stop - cut.start));
            }
        }
    }
    if let (Some(bc), Some(u)) = (bcs.first(), umi.first()) {
        format!("--soloType CB_UMI_Simple {} {}", bc, u)
    } else { String::new() }
}
fn format_simpleaf(indices: &Vec<Coordinate>) -> String {
    let mut xl: Vec<String> = Vec::new();
    for (idx, coord) in indices.iter().enumerate() {
        let mut x = format!("{}{{", idx + 1);
        for cut in &coord.rcv {
            let rt = cut.region.region_type.to_uppercase();
            let len = cut.stop - cut.start;
            if rt == "BARCODE" { x.push_str(&format!("b[{}]", len)); }
            else if rt == "UMI" { x.push_str(&format!("u[{}]", len)); }
            else if rt == "CDNA" { x.push_str(&format!("r[{}]", len)); }
        }
        x.push_str("x:}");
        xl.push(x);
    }
    xl.join("")
}
fn format_zumis(indices: &Vec<Coordinate>) -> String {
    let mut xl: Vec<String> = Vec::new();
    for coord in indices {
        let mut x = String::new();
        for cut in &coord.rcv {
            let rt = cut.region.region_type.to_uppercase();
            if rt == "BARCODE" {
                x.push_str(&format!("- BCS({}-{})\n", cut.start + 1, cut.stop));
            } else if rt == "UMI" {
                x.push_str(&format!("- UMI({}-{})\n", cut.start + 1, cut.stop));
            } else if rt == "CDNA" {
                x.push_str(&format!("- cDNA({}-{})\n", cut.start + 1, cut.stop));
            }
        }
        xl.push(x);
    }
    let mut out = xl.join("\n");
    if out.ends_with('\n') { out.pop(); }
    out
}
fn format_chromap(indices: &Vec<Coordinate>) -> String {
    let mut bc_fqs: Vec<String> = Vec::new();
    let mut bc_str: Vec<String> = Vec::new();
    let mut gdna_fqs: Vec<String> = Vec::new();
    let mut gdna_str: Vec<String> = Vec::new();
    for coord in indices {
        let strand_suffix = if coord.strand == "pos" { String::new() } else { ":-".to_string() };
        for cut in &coord.rcv {
            let rt = cut.region.region_type.to_uppercase();
            if rt == "BARCODE" {
                bc_fqs.push(coord.query_id.clone());
                bc_str.push(format!("bc:{}:{}{}", cut.start, cut.stop - 1, strand_suffix));
            } else if rt == "GDNA" {
                gdna_fqs.push(coord.query_id.clone());
                gdna_str.push(format!("{}:{}", cut.start, cut.stop - 1));
            }
        }
    }
    if bc_fqs.iter().collect::<HashSet<_>>().len() > 1 { panic!("chromap only supports barcodes from one fastq"); }
    if gdna_fqs.iter().collect::<HashSet<_>>().len() > 2 { panic!("chromap only supports genomic dna from two fastqs"); }
    let barcode_fq = bc_fqs.first().cloned().unwrap_or_default();
    let dedup_gdna_fqs = {
        let mut seen: HashSet<String> = HashSet::new();
        let mut out: Vec<String> = Vec::new();
        for r in &gdna_fqs {
            if !seen.contains(r) {
                out.push(r.clone());
                seen.insert(r.clone());
            }
        }
        out
    };
    let read1_fq = dedup_gdna_fqs.get(0).cloned().unwrap_or_default();
    let read2_fq = dedup_gdna_fqs.get(1).cloned().unwrap_or_default();
    let read_str = gdna_str.iter().enumerate().map(|(i, ele)| format!("r{}:{}", i+1, ele)).collect::<Vec<_>>().join(",");
    let bc_str_join = bc_str.join(",");
    format!("-1 {} -2 {} --barcode {} --read-format {},{}", read1_fq, read2_fq, barcode_fq, bc_str_join, read_str)
}
fn compute_relative(rcs: &Vec<RegionCoordinate>) -> Vec<RegionCoordinateDifference> {
    let mut d: Vec<RegionCoordinateDifference> = Vec::new();
    for obj in rcs {
        for fixed in rcs {
            if let Some(diff) = obj.difference(fixed) {
                d.push(RegionCoordinateDifference::new(obj.clone(), fixed.clone(), diff));
            }
        }
    }
    d
}
fn filter_differences(d: Vec<RegionCoordinateDifference>, filter_region_type: &str) -> Vec<RegionCoordinateDifference> {
    let mut f: Vec<RegionCoordinateDifference> = Vec::new();
    for rcd in d.into_iter() {
        if rcd.obj.region.region_type != filter_region_type && rcd.fixed.region.region_type == filter_region_type {
            f.push(rcd);
        }
    }
    f
}
fn format_relative(indices: &Vec<Coordinate>) -> String {
    let mut x = String::new();
    for coord in indices {
        let diffs = compute_relative(&coord.rcv);
        let mut filtered = filter_differences(diffs, "linker");
        filtered.sort_by_key(|diff| diff.obj.region.region_type.clone());
        for diff in filtered {
            x.push_str(&format!(
                "{}\t{}\t{}\t{}\t{}\n",
                diff.obj.region.region_id,
                diff.fixed.region.region_id,
                diff.rgncdiff.start,
                diff.rgncdiff.stop,
                diff.loc
            ));
        }
    }
    x
}
// Splitcode formatting: port essential behavior (forward/complement/reverse/rc groups)
#[derive(Clone)]
struct SplitRow { region_type: String, fmt: String }

fn format_splitcode(indices: &Vec<Coordinate>) -> String {
    use std::collections::HashMap;

    fn compute_relative(rcs: &Vec<RegionCoordinate>) -> Vec<RegionCoordinateDifference> {
        let mut d: Vec<RegionCoordinateDifference> = Vec::new();
        for obj in rcs {
            for fixed in rcs {
                if let Some(diff) = obj.difference(fixed) {
                    d.push(RegionCoordinateDifference::new(obj.clone(), fixed.clone(), diff));
                }
            }
        }
        d
    }

    fn filter_differences(d: Vec<RegionCoordinateDifference>, filter_region_type: &str) -> Vec<RegionCoordinateDifference> {
        let mut f: Vec<RegionCoordinateDifference> = Vec::new();
        for rcd in d.into_iter() {
            if rcd.obj.region.region_type != filter_region_type && rcd.fixed.region.region_type == filter_region_type {
                f.push(rcd);
            }
        }
        f
    }

    fn groupby_region_id(rgns: &Vec<RegionCoordinateDifference>) -> HashMap<String, (RegionCoordinate, Vec<RegionCoordinateDifference>)> {
        let mut d: HashMap<String, (RegionCoordinate, Vec<RegionCoordinateDifference>)> = HashMap::new();
        for rgn in rgns {
            let key = rgn.obj.region.region_id.clone();
            d.entry(key).and_modify(|(_, v)| v.push(rgn.clone())).or_insert((rgn.obj.clone(), vec![rgn.clone()]));
        }
        d
    }

    fn filter_groupby_region_type(g: &mut HashMap<String, (RegionCoordinate, Vec<RegionCoordinateDifference>)>) {
        let keys: Vec<String> = g.keys().cloned().collect();
        for k in keys {
            let (obj, _) = g.get(&k).unwrap();
            let t = obj.region.region_type.to_lowercase();
            if t != "umi" && t != "barcode" && t != "cdna" { g.remove(&k); }
        }
    }

    fn format_splitcode_row(obj: &RegionCoordinate, rgncdiffs: &Vec<RegionCoordinateDifference>, idx: i32, rev: bool, complement: bool) -> SplitRow {
        let mut e = String::new();
        if obj.region.region_type.to_lowercase() == "cdna" {
            if rev && !complement { e.push_str(&format!("<r_{}>", obj.region.region_id)); }
            else if rev && complement { e.push_str(&format!("<~rc_{}>", obj.region.region_id)); }
            else if !rev && complement { e.push_str(&format!("<~c_{}>", obj.region.region_id)); }
            else { e.push_str(&format!("<f_{}>", obj.region.region_id)); }
            if idx == 0 { e = format!("0:0{}", e); }
            else if idx == -1 { e = format!("{}0:-1", e); }
        } else {
            let tag = if rev && !complement { "r" }
                      else if rev && complement { "rc" }
                      else if !rev && complement { "c" }
                      else { "f" };
            e.push_str(&format!("<{}_{}[{}]>", tag, obj.region.region_type, obj.region.min_len));
        }

        let mut p1 = false;
        let mut m1 = false;
        let mut srtdiffs = rgncdiffs.clone();
        srtdiffs.sort_by_key(|x| x.rgncdiff.region.min_len);
        for diffs in srtdiffs.iter() {
            let fixed = &diffs.fixed.region;
            let loc = &diffs.loc;
            let diff = &diffs.rgncdiff;
            if fixed.region_type == "linker" {
                let minl = diff.region.min_len;
                let minl_str = if minl == 0 { String::new() } else { format!("{}", minl) };
                if loc == "+" && !p1 {
                    if rev && !complement { e = format!("{}{}{{{}r}}", e, minl_str, fixed.region_id); }
                    else if rev && complement { e = format!("{}{}{{{}rc}}", e, minl_str, fixed.region_id); }
                    else if !rev && complement { e = format!("{{{}c}}{}{}", fixed.region_id, minl_str, e); }
                    else { e = format!("{{{}f}}{}{}", fixed.region_id, minl_str, e); }
                    p1 = true;
                } else if loc == "-" && !m1 {
                    if rev && !complement { e = format!("{{{}r}}{}{}", fixed.region_id, minl_str, e); }
                    else if rev && complement { e = format!("{{{}rc}}{}{}", fixed.region_id, minl_str, e); }
                    else if !rev && complement { e = format!("{}{}{{{}c}}", e, minl_str, fixed.region_id); }
                    else { e = format!("{}{}{{{}f}}", e, minl_str, fixed.region_id); }
                    m1 = true;
                }
            }
        }
        SplitRow { region_type: obj.region.region_type.clone(), fmt: e }
    }

    let mut x = String::new();
    let mut e = String::new();
    for coord in indices {
        let d = compute_relative(&coord.rcv);
        let f = filter_differences(d, "linker");
        let mut g = groupby_region_id(&f);
        filter_groupby_region_type(&mut g);
        let gv: Vec<(RegionCoordinate, Vec<RegionCoordinateDifference>)> = g.into_values().collect();

        let mut frows: Vec<SplitRow> = Vec::new();
        let mut rrows: Vec<SplitRow> = Vec::new();
        let mut crows: Vec<SplitRow> = Vec::new();
        let mut rcrows: Vec<SplitRow> = Vec::new();

        for (i, (gb_obj, gb_rgncdiffs)) in gv.iter().enumerate() {
            let last = i + 1 == gv.len();
            let idx_val: i32 = if last { -1 } else { i as i32 };
            frows.push(format_splitcode_row(gb_obj, gb_rgncdiffs, idx_val, false, false));
            rrows.push(format_splitcode_row(gb_obj, gb_rgncdiffs, idx_val, true, false));
            crows.push(format_splitcode_row(gb_obj, gb_rgncdiffs, idx_val, false, true));
            rcrows.push(format_splitcode_row(gb_obj, gb_rgncdiffs, idx_val, true, true));
        }

        let mut g_frows: HashMap<String, Vec<String>> = HashMap::new();
        let mut g_crows: HashMap<String, Vec<String>> = HashMap::new();
        let mut g_rrows: HashMap<String, Vec<String>> = HashMap::new();
        let mut g_rcrows: HashMap<String, Vec<String>> = HashMap::new();
        for r in frows { g_frows.entry(r.region_type).or_default().push(r.fmt); }
        for r in crows { g_crows.entry(r.region_type).or_default().push(r.fmt); }
        for r in rrows { g_rrows.entry(r.region_type).or_default().push(r.fmt); }
        for r in rcrows { g_rcrows.entry(r.region_type).or_default().push(r.fmt); }

        for (_gr, v) in g_frows { e.push_str(&format!("@extract {}\n", v.join(","))); }
        for (_gr, v) in g_crows { e.push_str(&format!("@extract {}\n", v.join(","))); }
        for (_gr, v) in g_rrows { e.push_str(&format!("@extract {}\n", v.join(","))); }
        for (_gr, v) in g_rcrows { e.push_str(&format!("@extract {}\n", v.join(","))); }
    }
    x.push_str(&e);

    for coord in indices {
        x.push_str("groups\tids\ttags\tdistances\tlocations\n");
        let mut idx = 1;
        for cut in &coord.rcv {
            if cut.region.region_type == "linker" {
                x.push_str(&format!("group{}\t{}f\t{}\t3:3:3\t0:0:0\n", idx, cut.region.name, cut.region.sequence));
                let comp = utils::complement_seq(&cut.region.sequence);
                x.push_str(&format!("group{}\t{}c\t{}\t3:3:3\t0:0:0\n", idx, cut.region.name, comp));
                x.push_str(&format!("group{}\t{}r\t{}\t3:3:3\t0:0:0\n", idx, cut.region.name, cut.region.sequence.chars().rev().collect::<String>()));
                x.push_str(&format!("group{}\t{}rc\t{}\t3:3:3\t0:0:0\n", idx, cut.region.name, comp.chars().rev().collect::<String>()));
                idx += 1;
            }
        }
    }
    x
}
fn list_files_by_file_id(spec: &Assay, modality: &String, file_ids: &Vec<String>) -> HashMap<String, Vec<File>> {
    let mut files: HashMap<String, Vec<File>> = HashMap::new();
    let ids: HashSet<String> = file_ids.iter().cloned().collect();
    for read in spec.get_seqspec(modality) {
        if !read.files.is_empty() {
            for file in read.files {
                // parity with Python: membership against provided ids uses filename there
                if ids.contains(&file.filename) {
                    files.entry(read.read_id.clone()).or_default().push(file);
                }
            }
        }
    }
    files
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    #[test]
    fn test_index_by_reads() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let indices = get_index_by_reads(&spec, &modality);
        assert_eq!(indices.len(), 2); // RNA has 2 reads: rna_R1, rna_R2
        assert_eq!(indices[0].query_id, "rna_R1");
        assert_eq!(indices[1].query_id, "rna_R2");
        // R1 has barcode + UMI = 2 regions, R2 has cDNA = 1 region
        assert_eq!(indices[0].rcv.len(), 2);
        assert_eq!(indices[1].rcv.len(), 1);
    }

    #[test]
    fn test_index_by_read_ids() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let rna_reads = spec.get_seqspec("rna");
        assert!(!rna_reads.is_empty());
        let read_ids: Vec<String> = vec![rna_reads[0].read_id.clone()];
        let indices = get_index_by_read_ids(&spec, &modality, &read_ids);
        assert_eq!(indices.len(), 1);
        assert!(!indices[0].rcv.is_empty());
    }

    #[test]
    fn test_index_by_regions() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let indices = get_index_by_regions(&spec, &modality);
        assert_eq!(indices.len(), 1);
        assert_eq!(indices[0].query_id, "rna");
        assert_eq!(indices[0].query_type, "Region");
        // RNA library has 5 leaf regions
        assert_eq!(indices[0].rcv.len(), 5);
    }

    #[test]
    fn test_format_tab() {
        let indices = rna_indices();
        let result = format_index(&indices, &"tab".to_string(), &None);
        let lines: Vec<&str> = result.lines().collect();
        assert_eq!(lines.len(), 3);
        assert_eq!(lines[0], "rna_R1\tCell Barcode\tbarcode\t0\t16");
        assert_eq!(lines[1], "rna_R1\tumi\tumi\t16\t28");
        assert_eq!(lines[2], "rna_R2\tcdna\tcdna\t0\t102");
    }

    #[test]
    fn test_format_kb() {
        let indices = rna_indices();
        let result = format_index(&indices, &"kb".to_string(), &None);
        assert_eq!(result, "0,0,16:0,16,28:1,0,102");
    }

    #[test]
    fn test_seqspec_index_dispatch() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let ids: Vec<String> = vec![];
        let idtype = "read".to_string();
        let rev = false;
        let indices = seqspec_index(&spec, &modality, &ids, &idtype, &rev);
        assert_eq!(indices.len(), 2);
        assert_eq!(indices[0].query_id, "rna_R1");
        assert_eq!(indices[1].query_id, "rna_R2");
    }

    // ---- Format function tests ----

    fn rna_indices() -> Vec<Coordinate> {
        let spec = dogma_spec();
        get_index_by_reads(&spec, &"rna".to_string())
    }

    #[test]
    fn test_format_starsolo() {
        let indices = rna_indices();
        let result = format_index(&indices, &"starsolo".to_string(), &None);
        assert_eq!(
            result,
            "--soloType CB_UMI_Simple --soloCBstart 1 --soloCBlen 16 --soloUMIstart 17 --soloUMIlen 12"
        );
    }

    #[test]
    fn test_format_simpleaf() {
        let indices = rna_indices();
        let result = format_index(&indices, &"simpleaf".to_string(), &None);
        assert_eq!(result, "1{b[16]u[12]x:}2{r[102]x:}");
    }

    #[test]
    fn test_format_zumis() {
        let indices = rna_indices();
        let result = format_index(&indices, &"zumis".to_string(), &None);
        assert!(result.contains("BCS(1-16)"));
        assert!(result.contains("UMI(17-28)"));
        assert!(result.contains("cDNA(1-102)"));
    }

    #[test]
    fn test_format_kb_single() {
        let indices = rna_indices();
        let result = format_index(&indices, &"kb-single".to_string(), &None);
        // kb-single selects only the longest feature read
        assert_eq!(result, "0,0,16:0,16,28:1,0,102");
    }

    #[test]
    fn test_index_by_files() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let indices = get_index_by_files(&spec, &modality);
        assert!(!indices.is_empty());
        for coord in &indices {
            assert_eq!(coord.query_type, "File");
        }
    }

    #[test]
    fn test_index_by_region_ids() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let lib = spec.get_libspec("rna").unwrap();
        let region_id = lib.region_id.clone();
        let indices = get_index_by_region_ids(&spec, &modality, &vec![region_id]);
        assert_eq!(indices.len(), 1);
        assert_eq!(indices[0].query_type, "Region");
    }

    #[test]
    fn test_index_different_modalities() {
        let spec = dogma_spec();
        for modality in ["rna", "atac", "protein", "tag"] {
            let m = modality.to_string();
            let indices = get_index_by_reads(&spec, &m);
            assert!(!indices.is_empty(), "modality {} should have indices", modality);
        }
    }

    #[test]
    fn test_filter_index_no_overlap() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let indices = get_index_by_reads(&spec, &modality);
        let orig_count: usize = indices.iter().map(|i| i.rcv.len()).sum();
        let filtered = filter_index_no_overlap(indices);
        // Filtered should have same or fewer total region coordinates
        let filt_count: usize = filtered.iter().map(|i| i.rcv.len()).sum();
        assert!(filt_count <= orig_count);
    }

    #[test]
    fn test_index_dispatch_file_selector() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let ids: Vec<String> = vec![];
        let idtype = "file".to_string();
        let rev = false;
        let indices = seqspec_index(&spec, &modality, &ids, &idtype, &rev);
        assert!(!indices.is_empty());
    }

    #[test]
    fn test_index_dispatch_region_with_ids() {
        let spec = dogma_spec();
        let modality = "rna".to_string();
        let lib = spec.get_libspec("rna").unwrap();
        let ids = vec![lib.region_id.clone()];
        let idtype = "region".to_string();
        let rev = false;
        let indices = seqspec_index(&spec, &modality, &ids, &idtype, &rev);
        assert_eq!(indices.len(), 1);
    }
}