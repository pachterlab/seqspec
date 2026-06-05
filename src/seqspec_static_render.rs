use crate::models::assay::Assay;
use crate::seqspec_html::{self, ModalityView, RegionView};
use std::collections::BTreeSet;

const READ_COLORS: [&str; 5] = ["#1e40af", "#059669", "#d97706", "#dc2626", "#7c3aed"];
const FONT_FAMILY: &str = "Menlo, Monaco, Consolas, monospace";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LabelMode {
    Name,
    RegionId,
    Length,
    NameLength,
    None,
}

impl LabelMode {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "name" => Ok(Self::Name),
            "region_id" => Ok(Self::RegionId),
            "length" => Ok(Self::Length),
            "name+length" => Ok(Self::NameLength),
            "none" => Ok(Self::None),
            _ => Err(format!(
                "Unsupported label: {}. Must be one of name, region_id, length, name+length, none",
                value
            )),
        }
    }
}

struct Canvas {
    width: f64,
    height: f64,
    left: f64,
    right: f64,
    top: f64,
    bottom: f64,
    row_h: f64,
    global_xmin: f64,
    global_xmax: f64,
}

impl Canvas {
    fn x(&self, bp: f64) -> f64 {
        let span = (self.global_xmax - self.global_xmin).max(1.0);
        self.left + (bp - self.global_xmin) * (self.width - self.left - self.right) / span
    }
}

pub fn render_static(spec: &Assay, fmt: &str, label: &str) -> Result<Vec<u8>, String> {
    let mode = LabelMode::parse(label)?;
    let svg = render_svg(spec, mode)?;

    match fmt {
        "seqspec-png" => svg_to_png(&svg),
        "seqspec-pdf" => svg_to_pdf(&svg),
        _ => Err(format!("Unsupported static format: {}", fmt)),
    }
}

pub fn render_svg(spec: &Assay, label: LabelMode) -> Result<String, String> {
    let payload = seqspec_html::build_seqspec_view_data(spec)?;
    let canvas = canvas_for_payload(&payload, label);
    let mut out = String::new();
    let mut sequence_types = BTreeSet::new();

    out.push_str(&format!(
        r##"<svg xmlns="http://www.w3.org/2000/svg" width="{:.0}" height="{:.0}" viewBox="0 0 {:.0} {:.0}">
<defs>
  <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill="#1e40af"/></marker>
  <marker id="arrow-green" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill="#059669"/></marker>
  <marker id="arrow-orange" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill="#d97706"/></marker>
  <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill="#dc2626"/></marker>
  <marker id="arrow-purple" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill="#7c3aed"/></marker>
</defs>
<rect x="0" y="0" width="{:.0}" height="{:.0}" fill="white"/>
"##,
        canvas.width, canvas.height, canvas.width, canvas.height, canvas.width, canvas.height
    ));

    text(
        &mut out,
        canvas.width / 2.0,
        44.0,
        &payload.assay_id,
        30.0,
        "#000000",
        TextAnchor::Middle,
        None,
    );

    for (row_idx, modality) in payload.modalities.iter().enumerate() {
        draw_modality(
            &mut out,
            &canvas,
            modality,
            row_idx,
            label,
            &mut sequence_types,
        );
    }

    draw_axis(&mut out, &canvas);
    draw_legend(&mut out, &canvas, &sequence_types);
    out.push_str("</svg>\n");
    Ok(out)
}

fn canvas_for_payload(payload: &seqspec_html::SeqspecViewData, label: LabelMode) -> Canvas {
    let mut global_xmin = 0.0_f64;
    let mut global_xmax = payload
        .modalities
        .iter()
        .map(|m| m.total_bp as f64)
        .fold(1.0_f64, f64::max);

    for modality in &payload.modalities {
        for read in &modality.reads {
            global_xmin = global_xmin.min(read.start as f64).min(read.end as f64);
            global_xmax = global_xmax.max(read.start as f64).max(read.end as f64);
        }
    }

    let pad = (global_xmax - global_xmin).mul_add(0.02, 0.0).max(5.0);
    global_xmin -= pad;
    global_xmax += pad;

    let max_lane_capacity = payload
        .modalities
        .iter()
        .map(|modality| callout_lane_capacity(&modality.regions, label))
        .max()
        .unwrap_or(3);
    let row_h = (310.0_f64).max(235.0 + 60.0 * max_lane_capacity as f64);
    let top = (80.0_f64).max(70.0 + 50.0 * max_lane_capacity as f64);
    let bottom = 90.0;
    Canvas {
        width: 2400.0,
        height: top + bottom + row_h * payload.modalities.len().max(1) as f64,
        left: 250.0,
        right: 360.0,
        top,
        bottom,
        row_h,
        global_xmin,
        global_xmax,
    }
}

fn draw_modality(
    out: &mut String,
    canvas: &Canvas,
    modality: &ModalityView,
    row_idx: usize,
    label: LabelMode,
    sequence_types: &mut BTreeSet<String>,
) {
    let row_y = canvas.top + row_idx as f64 * canvas.row_h;
    let bar_y = row_y + 110.0;
    let bar_h = 30.0;

    text(
        out,
        canvas.left - 65.0,
        bar_y + bar_h / 2.0 + 11.0,
        &modality.modality,
        42.0,
        "#000000",
        TextAnchor::End,
        None,
    );

    draw_group_regions(out, canvas, modality, bar_y);

    for region in &modality.regions {
        sequence_types.insert(region.sequence_type.clone());
        let x = canvas.x(region.bp_start as f64);
        let w = (canvas.x(region.bp_end as f64) - x).max(0.5);
        rect(
            out,
            x,
            bar_y,
            w,
            bar_h,
            sequence_type_fill(&region.sequence_type),
            sequence_type_stroke(&region.sequence_type),
            1.4,
        );
    }

    draw_region_labels(out, canvas, &modality.regions, label, bar_y, bar_h);
    draw_reads(out, canvas, modality, bar_y, bar_h);
}

fn draw_group_regions(out: &mut String, canvas: &Canvas, modality: &ModalityView, bar_y: f64) {
    let group_regions: Vec<&RegionView> = modality
        .region_nodes
        .iter()
        .filter(|region| !region.is_leaf)
        .collect();
    let max_depth = group_regions
        .iter()
        .map(|region| region.depth)
        .max()
        .unwrap_or(0);
    let group_top = bar_y - 45.0 - max_depth as f64 * 18.0;

    for region in group_regions {
        let x = canvas.x(region.bp_start as f64);
        let w = (canvas.x(region.bp_end as f64) - x).max(0.5);
        let y = group_top + region.depth as f64 * 18.0;
        rect(out, x, y, w, 9.0, "white", "#848a92", 1.0);
        if w > 380.0 {
            text(
                out,
                x + 5.0,
                y - 3.0,
                &region.name,
                19.0,
                "#848a92",
                TextAnchor::Start,
                None,
            );
        }
    }
}

fn draw_region_labels(
    out: &mut String,
    canvas: &Canvas,
    regions: &[RegionView],
    label_mode: LabelMode,
    bar_y: f64,
    bar_h: f64,
) {
    let mut callout_count = 0_usize;
    let capacity = callout_lane_capacity(regions, label_mode);
    let mut above_lanes = vec![f64::NEG_INFINITY; capacity];
    let mut below_lanes = vec![f64::NEG_INFINITY; capacity];

    for region in regions {
        let label = region_label(region, label_mode);
        if label.is_empty() {
            continue;
        }

        let start = canvas.x(region.bp_start as f64);
        let end = canvas.x(region.bp_end as f64);
        let center = start + (end - start) / 2.0;

        if is_short_region(region, &label) {
            let above = callout_count % 2 == 1;
            let lanes = if above {
                &mut above_lanes
            } else {
                &mut below_lanes
            };
            let (lane, text_x) = choose_callout_lane(center, &label, lanes);
            let (anchor_y, text_y) = if above {
                (bar_y, bar_y - 38.0 - 44.0 * lane as f64)
            } else {
                (bar_y + bar_h, bar_y + 64.0 + 46.0 * lane as f64)
            };
            let label_left = text_x - 8.0;
            line(
                out, center, anchor_y, center, text_y, "#c5cbd3", 0.9, None, 1.0,
            );
            line(
                out, center, text_y, label_left, text_y, "#c5cbd3", 0.9, None, 1.0,
            );
            text(
                out,
                text_x,
                text_y + 6.0,
                &label,
                24.0,
                "#4a5058",
                TextAnchor::Start,
                None,
            );
            callout_count += 1;
        } else {
            text(
                out,
                center,
                bar_y + bar_h / 2.0 + 8.0,
                &label,
                22.0,
                "#2f343b",
                TextAnchor::Middle,
                None,
            );
        }
    }
}

fn draw_reads(out: &mut String, canvas: &Canvas, modality: &ModalityView, bar_y: f64, bar_h: f64) {
    let pos_reads: Vec<_> = modality
        .reads
        .iter()
        .filter(|read| read.strand == "pos")
        .collect();
    let neg_reads: Vec<_> = modality
        .reads
        .iter()
        .filter(|read| read.strand == "neg")
        .collect();

    let (above_callout_lanes, below_callout_lanes) =
        estimate_callout_lane_counts(&modality.regions, LabelMode::NameLength, canvas);
    let pos_base_y = bar_y - (80.0_f64).max(70.0 + 50.0 * above_callout_lanes as f64);
    let neg_base_y = bar_y + (130.0_f64).max(112.0 + 52.0 * below_callout_lanes as f64);

    for (idx, read) in pos_reads.iter().enumerate() {
        let color = READ_COLORS[idx % READ_COLORS.len()];
        let y = pos_base_y - 45.0 * idx as f64;
        let start = canvas.x(read.start as f64);
        let end = canvas.x(read.end as f64);
        rect_alpha(
            out,
            start.min(end),
            y,
            (end - start).abs().max(0.5),
            (bar_y - y).max(0.5),
            color,
            0.07,
        );
        line(out, start, bar_y, start, y, color, 1.3, Some("4 4"), 0.45);
        line(out, end, bar_y, end, y, color, 1.1, Some("4 4"), 0.32);
        arrow(out, start, y, end, y, color, idx);
        let label = read_label(&read.label, &read.read_id, read.start, read.end);
        text(
            out,
            start + 6.0,
            y - 10.0,
            &label,
            24.0,
            color,
            TextAnchor::Start,
            None,
        );
    }

    for (idx, read) in neg_reads.iter().enumerate() {
        let color_idx = pos_reads.len() + idx;
        let color = READ_COLORS[color_idx % READ_COLORS.len()];
        let y = neg_base_y + 45.0 * idx as f64;
        let start = canvas.x(read.start as f64);
        let end = canvas.x(read.end as f64);
        rect_alpha(
            out,
            start.min(end),
            bar_y + bar_h,
            (end - start).abs().max(0.5),
            (y - (bar_y + bar_h)).max(0.5),
            color,
            0.07,
        );
        line(
            out,
            end,
            bar_y + bar_h,
            end,
            y,
            color,
            1.3,
            Some("4 4"),
            0.45,
        );
        line(
            out,
            start,
            bar_y + bar_h,
            start,
            y,
            color,
            1.1,
            Some("4 4"),
            0.32,
        );
        arrow(out, end, y, start, y, color, color_idx);
        let label = read_label(&read.label, &read.read_id, read.start, read.end);
        text(
            out,
            end - 6.0,
            y + 26.0,
            &label,
            24.0,
            color,
            TextAnchor::End,
            None,
        );
    }
}

fn draw_axis(out: &mut String, canvas: &Canvas) {
    let y = canvas.height - canvas.bottom + 12.0;
    let x0 = canvas.left;
    let x1 = canvas.width - canvas.right;
    line(out, x0, y, x1, y, "#222222", 1.8, None, 1.0);

    let first = ((canvas.global_xmin / 25.0).ceil() as i64) * 25;
    let last = ((canvas.global_xmax / 25.0).floor() as i64) * 25;
    for tick in (first..=last).step_by(25) {
        let x = canvas.x(tick as f64);
        line(out, x, y, x, y + 10.0, "#222222", 1.5, None, 1.0);
        text(
            out,
            x,
            y + 40.0,
            &tick.to_string(),
            26.0,
            "#222222",
            TextAnchor::Middle,
            None,
        );
    }

    text(
        out,
        (x0 + x1) / 2.0,
        y + 78.0,
        "# nucleotides",
        28.0,
        "#000000",
        TextAnchor::Middle,
        None,
    );
}

fn draw_legend(out: &mut String, canvas: &Canvas, sequence_types: &BTreeSet<String>) {
    if sequence_types.is_empty() {
        return;
    }
    let x = canvas.width - canvas.right + 70.0;
    let h = 78.0 + 40.0 * sequence_types.len() as f64;
    let rect_y = 36.0;
    let y = rect_y + 32.0;
    rect(out, x - 18.0, y - 32.0, 210.0, h, "white", "#d1d5db", 2.0);
    text(
        out,
        x,
        y,
        "Region type",
        24.0,
        "#000000",
        TextAnchor::Start,
        None,
    );

    for (idx, sequence_type) in sequence_types.iter().enumerate() {
        let row_y = y + 38.0 + idx as f64 * 40.0;
        rect(
            out,
            x,
            row_y - 18.0,
            58.0,
            22.0,
            sequence_type_fill(sequence_type),
            sequence_type_stroke(sequence_type),
            2.0,
        );
        text(
            out,
            x + 82.0,
            row_y,
            sequence_type,
            26.0,
            "#000000",
            TextAnchor::Start,
            None,
        );
    }
}

fn region_label(region: &RegionView, mode: LabelMode) -> String {
    match mode {
        LabelMode::Name => region.name.clone(),
        LabelMode::RegionId => region.region_id.clone(),
        LabelMode::Length => region.len.to_string(),
        LabelMode::NameLength => format!("{} ({})", region.name, region.len),
        LabelMode::None => String::new(),
    }
}

fn read_label(label: &str, read_id: &str, start: i64, end: i64) -> String {
    let display = if label.is_empty() { read_id } else { label };
    format!("{} ({})", display, (end - start).abs())
}

fn is_short_region(region: &RegionView, text: &str) -> bool {
    let len = (region.bp_end - region.bp_start).max(0) as f64;
    len < 14.0_f64.max(text.len() as f64 * 2.6)
}

fn short_region_label_count(regions: &[RegionView], label_mode: LabelMode) -> usize {
    regions
        .iter()
        .filter(|region| {
            let label = region_label(region, label_mode);
            !label.is_empty() && is_short_region(region, &label)
        })
        .count()
}

fn callout_lane_capacity(regions: &[RegionView], label_mode: LabelMode) -> usize {
    let count = short_region_label_count(regions, label_mode);
    ((count + 1) / 2).clamp(3, 6)
}

fn estimate_callout_lane_counts(
    regions: &[RegionView],
    label_mode: LabelMode,
    canvas: &Canvas,
) -> (usize, usize) {
    let capacity = callout_lane_capacity(regions, label_mode);
    let mut above_lanes = vec![f64::NEG_INFINITY; capacity];
    let mut below_lanes = vec![f64::NEG_INFINITY; capacity];
    let mut above_used = 0_usize;
    let mut below_used = 0_usize;
    let mut callout_count = 0_usize;

    for region in regions {
        let label = region_label(region, label_mode);
        if label.is_empty() || !is_short_region(region, &label) {
            continue;
        }

        let start = canvas.x(region.bp_start as f64);
        let end = canvas.x(region.bp_end as f64);
        let center = start + (end - start) / 2.0;
        if callout_count % 2 == 1 {
            let (lane, _) = choose_callout_lane(center, &label, &mut above_lanes);
            above_used = above_used.max(lane + 1);
        } else {
            let (lane, _) = choose_callout_lane(center, &label, &mut below_lanes);
            below_used = below_used.max(lane + 1);
        }
        callout_count += 1;
    }

    (above_used, below_used)
}

fn estimate_label_width_px(text: &str) -> f64 {
    (text.len() as f64 * 16.0).max(40.0)
}

fn choose_callout_lane(center: f64, text: &str, lane_ends: &mut [f64]) -> (usize, f64) {
    let mut text_x = center + 26.0;
    let gap = 22.0;
    let label_end = text_x + estimate_label_width_px(text);

    for (lane, lane_end) in lane_ends.iter_mut().enumerate() {
        if text_x >= *lane_end + gap {
            *lane_end = label_end;
            return (lane, text_x);
        }
    }

    let lane = lane_ends
        .iter()
        .enumerate()
        .min_by(|(_, left), (_, right)| left.total_cmp(right))
        .map(|(idx, _)| idx)
        .unwrap_or(0);
    text_x = lane_ends[lane] + gap;
    lane_ends[lane] = text_x + estimate_label_width_px(text);
    (lane, text_x)
}

fn svg_to_png(svg: &str) -> Result<Vec<u8>, String> {
    let mut options = resvg::usvg::Options::default();
    options.fontdb_mut().load_system_fonts();
    let tree = resvg::usvg::Tree::from_str(svg, &options).map_err(|err| err.to_string())?;
    let size = tree.size().to_int_size();
    let mut pixmap = resvg::tiny_skia::Pixmap::new(size.width(), size.height())
        .ok_or_else(|| "cannot create PNG pixmap".to_string())?;
    resvg::render(
        &tree,
        resvg::tiny_skia::Transform::default(),
        &mut pixmap.as_mut(),
    );
    pixmap.encode_png().map_err(|err| err.to_string())
}

fn svg_to_pdf(svg: &str) -> Result<Vec<u8>, String> {
    let mut options = svg2pdf::usvg::Options::default();
    options.fontdb_mut().load_system_fonts();
    let tree = svg2pdf::usvg::Tree::from_str(svg, &options).map_err(|err| err.to_string())?;
    svg2pdf::to_pdf(
        &tree,
        svg2pdf::ConversionOptions::default(),
        svg2pdf::PageOptions::default(),
    )
    .map_err(|err| err.to_string())
}

fn sequence_type_fill(sequence_type: &str) -> &'static str {
    match sequence_type {
        "onlist" => "#bbf7d0",
        "random" => "#bfdbfe",
        _ => "#e2e5e9",
    }
}

fn sequence_type_stroke(sequence_type: &str) -> &'static str {
    match sequence_type {
        "onlist" => "#4ade80",
        "random" => "#60a5fa",
        _ => "#b0b5bc",
    }
}

fn arrow_marker(color_idx: usize) -> &'static str {
    match color_idx % READ_COLORS.len() {
        0 => "arrow-blue",
        1 => "arrow-green",
        2 => "arrow-orange",
        3 => "arrow-red",
        _ => "arrow-purple",
    }
}

fn rect(out: &mut String, x: f64, y: f64, w: f64, h: f64, fill: &str, stroke: &str, sw: f64) {
    out.push_str(&format!(
        r#"<rect x="{x:.3}" y="{y:.3}" width="{w:.3}" height="{h:.3}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.3}"/>"#
    ));
    out.push('\n');
}

fn rect_alpha(out: &mut String, x: f64, y: f64, w: f64, h: f64, fill: &str, opacity: f64) {
    out.push_str(&format!(
        r#"<rect x="{x:.3}" y="{y:.3}" width="{w:.3}" height="{h:.3}" fill="{fill}" fill-opacity="{opacity:.3}" stroke="none"/>"#
    ));
    out.push('\n');
}

fn line(
    out: &mut String,
    x1: f64,
    y1: f64,
    x2: f64,
    y2: f64,
    color: &str,
    width: f64,
    dash: Option<&str>,
    opacity: f64,
) {
    let dash = dash
        .map(|value| format!(r#" stroke-dasharray="{value}""#))
        .unwrap_or_default();
    out.push_str(&format!(
        r#"<line x1="{x1:.3}" y1="{y1:.3}" x2="{x2:.3}" y2="{y2:.3}" stroke="{color}" stroke-width="{width:.3}" stroke-opacity="{opacity:.3}"{dash}/>"#
    ));
    out.push('\n');
}

fn arrow(out: &mut String, x1: f64, y1: f64, x2: f64, y2: f64, color: &str, color_idx: usize) {
    out.push_str(&format!(
        r#"<line x1="{x1:.3}" y1="{y1:.3}" x2="{x2:.3}" y2="{y2:.3}" stroke="{color}" stroke-width="3.2" marker-end="url(#{})"/>"#,
        arrow_marker(color_idx)
    ));
    out.push('\n');
}

#[derive(Clone, Copy)]
enum TextAnchor {
    Start,
    Middle,
    End,
}

impl TextAnchor {
    fn as_svg(self) -> &'static str {
        match self {
            Self::Start => "start",
            Self::Middle => "middle",
            Self::End => "end",
        }
    }
}

fn text(
    out: &mut String,
    x: f64,
    y: f64,
    value: &str,
    size: f64,
    color: &str,
    anchor: TextAnchor,
    transform: Option<String>,
) {
    let transform = transform
        .map(|value| format!(r#" transform="{value}""#))
        .unwrap_or_default();
    out.push_str(&format!(
        r#"<text x="{x:.3}" y="{y:.3}" font-family="{FONT_FAMILY}" font-size="{size:.3}" fill="{color}" text-anchor="{}"{transform}>{}</text>"#,
        anchor.as_svg(),
        escape_xml(value)
    ));
    out.push('\n');
}

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
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
    fn test_render_svg_contains_expected_labels_and_reads() {
        let svg = render_svg(&dogma_spec(), LabelMode::NameLength).unwrap();
        assert!(svg.contains("DOGMAseq-DIG"));
        assert!(svg.contains("Cell Barcode (16)"));
        assert!(svg.contains("Region type"));
        assert!(svg.contains("rna Read 2 (102)"));
    }

    #[test]
    fn test_render_png_returns_png_bytes() {
        let bytes = render_static(&dogma_spec(), "seqspec-png", "name").unwrap();
        assert!(bytes.starts_with(b"\x89PNG\r\n\x1a\n"));
    }

    #[test]
    fn test_render_pdf_returns_pdf_bytes() {
        let bytes = render_static(&dogma_spec(), "seqspec-pdf", "name").unwrap();
        assert!(bytes.starts_with(b"%PDF-"));
    }
}
