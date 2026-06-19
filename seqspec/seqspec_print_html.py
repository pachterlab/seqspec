"""Render seqspec HTML views.

This module renders a single self-contained HTML page that shows the library
geometry for each modality and lets the user inspect metadata by selecting
regions and reads in the diagram.
"""

import json
from importlib.resources import files
from typing import Any

from seqspec.Assay import Assay
from seqspec.Region import Region, project_regions_to_coordinates
from seqspec.region_type import region_type_display

REPOSITORY_URL = "https://github.com/pachterlab/seqspec"


def print_seqspec_html(spec: Assay) -> str:
    """Render a self-contained HTML view for a seqspec assay."""
    payload = build_seqspec_view_data(spec)
    return render_seqspec_html(payload, spec.seqspec_version or "")


def build_seqspec_view_data(spec: Assay) -> dict[str, Any]:
    """Build the JSON payload consumed by the seqspec HTML viewer."""
    return {
        "assay_id": spec.assay_id,
        "assay_name": spec.name,
        "seqspec_version": spec.seqspec_version,
        "doi": spec.doi,
        "date": spec.date,
        "description": spec.description,
        "lib_struct": spec.lib_struct,
        "modalities": [
            build_modality_view(spec, modality) for modality in spec.modalities
        ],
    }


def build_modality_view(spec: Assay, modality: str) -> dict[str, Any]:
    """Build the HTML view payload for one modality."""
    libspec = spec.get_libspec(modality)
    if libspec is None:
        raise ValueError(f"modality '{modality}' not found in library_spec")

    region_nodes, regions, total_bp = region_views(libspec)
    reads = []
    for read in spec.get_seqspec(modality):
        projected = project_read(libspec, read)
        if projected is not None:
            reads.append(projected)

    return {
        "modality": modality,
        "library_region_id": libspec.region_id,
        "total_bp": total_bp,
        "sequence_protocols": protocol_rows(
            spec.sequence_protocol, modality, "protocol_id"
        ),
        "sequence_kits": protocol_rows(spec.sequence_kit, modality, "kit_id"),
        "library_protocols": protocol_rows(
            spec.library_protocol, modality, "protocol_id"
        ),
        "library_kits": protocol_rows(spec.library_kit, modality, "kit_id"),
        "region_nodes": region_nodes,
        "regions": regions,
        "reads": reads,
    }


def region_views(
    libspec: Region,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Build both the full region tree and the flattened leaf regions."""

    region_nodes, leaf_regions, total_bp = walk_regions(
        libspec.regions, depth=0, bp_start=0
    )
    return region_nodes, leaf_regions, total_bp


def walk_regions(
    regions: list[Region],
    depth: int,
    bp_start: int,
    parent_region_id: str | None = None,
    path_region_ids: list[str] | None = None,
    path_names: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Walk a region tree and return region nodes, leaf regions, and the next bp offset."""
    region_nodes: list[dict[str, Any]] = []
    leaf_regions: list[dict[str, Any]] = []
    current_bp = bp_start

    for region in regions:
        region_path_ids = [*(path_region_ids or []), region.region_id]
        region_path_names = [*(path_names or []), region.name]
        start = current_bp

        if region.regions:
            child_nodes, child_leaves, current_bp = walk_regions(
                region.regions,
                depth=depth + 1,
                bp_start=current_bp,
                parent_region_id=region.region_id,
                path_region_ids=region_path_ids,
                path_names=region_path_names,
            )
            end = current_bp
            region_nodes.append(
                region_node(
                    region=region,
                    depth=depth,
                    parent_region_id=parent_region_id,
                    path_region_ids=region_path_ids,
                    path_names=region_path_names,
                    start=start,
                    end=end,
                )
            )
            region_nodes.extend(child_nodes)
            leaf_regions.extend(child_leaves)
        else:
            end = current_bp + region.max_len
            node = region_node(
                region=region,
                depth=depth,
                parent_region_id=parent_region_id,
                path_region_ids=region_path_ids,
                path_names=region_path_names,
                start=start,
                end=end,
            )
            current_bp = end
            region_nodes.append(node)
            leaf_regions.append(node)

    return region_nodes, leaf_regions, current_bp


def region_node(
    region: Region,
    depth: int,
    parent_region_id: str | None,
    path_region_ids: list[str],
    path_names: list[str],
    start: int,
    end: int,
) -> dict[str, Any]:
    """Build one serialized region node."""
    return {
        "region_id": region.region_id,
        "region_type": region_type_display(region.region_type),
        "name": region.name,
        "sequence_type": str(region.sequence_type),
        "sequence": region.sequence,
        "min_len": region.min_len,
        "max_len": region.max_len,
        "len": end - start,
        "bp_start": start,
        "bp_end": end,
        "depth": depth,
        "parent_region_id": parent_region_id,
        "path_region_ids": path_region_ids,
        "path_names": path_names,
        "is_leaf": len(region.regions) == 0,
        "child_region_ids": [child.region_id for child in region.regions],
        "onlist": onlist_row(region.onlist),
    }


def project_read(libspec: Region, read) -> dict[str, Any] | None:
    """Project one read onto the library coordinate system."""
    leaves = libspec.get_leaves_with_region_id(read.primer_id)
    try:
        primer_index = next(
            index
            for index, leaf in enumerate(leaves)
            if leaf.region_id == read.primer_id
        )
    except StopIteration:
        return None
    cuts = project_regions_to_coordinates(leaves)
    primer = cuts[primer_index]

    if read.strand == "pos":
        start = primer.stop
        end = start + read.max_len
    else:
        end = primer.start
        start = end - read.max_len

    return {
        "read_id": read.read_id,
        "name": read.name,
        "label": read.name,
        "primer_id": read.primer_id,
        "min_len": read.min_len,
        "max_len": read.max_len,
        "strand": read.strand,
        "start": start,
        "end": end,
        "files": [file_row(file) for file in read.files],
    }


def protocol_rows(entries: Any, modality: str, id_key: str) -> list[dict[str, Any]]:
    """Collect protocol or kit metadata rows for one modality."""
    if entries is None:
        return []
    rows = []
    if isinstance(entries, str):
        return [{id_key: entries, "name": entries}]
    for entry in entries:
        if getattr(entry, "modality", None) != modality:
            continue
        row = {id_key: getattr(entry, id_key, ""), "name": getattr(entry, "name", None)}
        rows.append(row)
    return rows


def onlist_row(onlist) -> dict[str, Any] | None:
    """Convert an onlist object into a JSON row."""
    if onlist is None:
        return None
    return {
        "file_id": onlist.file_id,
        "filename": onlist.filename,
        "filetype": onlist.filetype,
        "filesize": onlist.filesize,
        "url": onlist.url,
        "urltype": onlist.urltype,
        "md5": onlist.md5,
    }


def file_row(file) -> dict[str, Any]:
    """Convert a read file into a JSON row."""
    return {
        "file_id": file.file_id,
        "filename": file.filename,
        "filetype": file.filetype,
        "filesize": file.filesize,
        "url": file.url,
        "urltype": file.urltype,
        "md5": file.md5,
    }


def render_seqspec_html(payload: dict[str, Any], tool_version: str) -> str:
    """Render the final HTML page."""
    template = asset_text("template.html")
    style = asset_text("style.css")
    app = asset_text("app.js")
    report_json = escape_script_json(json.dumps(payload, ensure_ascii=False))
    repository_json = json.dumps(REPOSITORY_URL)
    version_json = json.dumps(tool_version)

    return (
        template.replace("__STYLE__", style)
        .replace("__APP__", app)
        .replace("__DATA__", report_json)
        .replace("__REPOSITORY__", repository_json)
        .replace("__TOOL_VERSION__", version_json)
    )


def asset_text(name: str) -> str:
    """Read a packaged asset file."""
    return files("seqspec.report_assets").joinpath(name).read_text(encoding="utf-8")


def escape_script_json(value: str) -> str:
    """Escape JSON before embedding it in a script tag."""
    return value.replace("</", "<\\/")
