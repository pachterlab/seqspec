"""Build and validate the examples docs tree.

This module keeps ``docs/examples`` in one consistent shape:

1. maintained canonical examples under ``assays``, ``reads``, and ``regions``
2. a generated static site under ``site``

The build step is designed to be repeatable. It rewrites the canonical YAML,
writes a manifest, and renders the site.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from seqspec.seqspec_check import seqspec_check
from seqspec.seqspec_print_html import print_seqspec_html
from seqspec.utils import load_spec, safe_load_strip_tags

MANIFEST_VERSION = 1
ANCHOR_REGION_TYPES = {
    "illumina_p5",
    "illumina_p7",
    "truseq_read1",
    "truseq_read2",
    "nextera_read1",
    "nextera_read2",
    "s5",
    "s7",
}
READ_CONTAINER_PATTERN = re.compile(
    r"(?i)(^|[^a-z0-9])(r[12]|i[12]|read\s*[12]|index\s*[12])([^a-z0-9]|$)"
)
POSITIVE_READ_HINT = re.compile(r"(?i)(r1|i1|read\s*1|index\s*1|i7)")
NEGATIVE_READ_HINT = re.compile(r"(?i)(r2|i2|read\s*2|index\s*2|i5)")
PLACEHOLDER_MD5_VALUES = {"", "md5", None}


@dataclass(frozen=True)
class ExamplePaths:
    """Resolved paths for the examples tree."""

    repo_root: Path
    docs_examples: Path
    assays_dir: Path
    reads_dir: Path
    regions_dir: Path
    site_dir: Path
    site_assays_dir: Path
    manifest_path: Path
    readme_path: Path


def example_paths(repo_root: Path | None = None) -> ExamplePaths:
    """Build the path bundle used throughout the examples tooling."""
    root = repo_root or Path(__file__).resolve().parent.parent
    docs_examples = root / "docs" / "examples"
    site_dir = docs_examples / "site"
    return ExamplePaths(
        repo_root=root,
        docs_examples=docs_examples,
        assays_dir=docs_examples / "assays",
        reads_dir=docs_examples / "reads",
        regions_dir=docs_examples / "regions",
        site_dir=site_dir,
        site_assays_dir=site_dir / "assays",
        manifest_path=docs_examples / "examples.yaml",
        readme_path=docs_examples / "README.md",
    )


def build_examples_tree(repo_root: Path | None = None) -> None:
    """Build the consolidated examples tree."""
    paths = example_paths(repo_root)
    ensure_example_directories(paths)
    normalize_canonical_examples(paths)
    manifest = build_manifest(paths)
    write_yaml(paths.manifest_path, manifest)
    write_examples_readme(paths, manifest)
    write_site(paths, manifest)
    remove_superseded_example_sources(paths)


def validate_examples_tree(repo_root: Path | None = None) -> list[str]:
    """Validate the generated examples tree and return any problems."""
    paths = example_paths(repo_root)
    errors: list[str] = []

    if not paths.manifest_path.exists():
        return [f"missing manifest: {paths.manifest_path}"]

    manifest = yaml.safe_load(paths.manifest_path.read_text()) or {}
    assays = manifest.get("assays", [])

    for assay in assays:
        canonical_path = paths.docs_examples / assay["canonical_path"]
        if not canonical_path.exists():
            errors.append(f"missing canonical assay: {canonical_path}")
            continue

        spec = load_spec(canonical_path, strict=False)
        if spec.seqspec_version != "0.4.0":
            errors.append(f"canonical assay does not declare 0.4.0: {canonical_path}")

        raw_text = canonical_path.read_text()
        for token in (
            "!Assay",
            "!Read",
            "!Region",
            "!Onlist",
            "parent_id:",
            "location:",
        ):
            if token in raw_text:
                errors.append(f"legacy field '{token}' found in {canonical_path}")

        try:
            html = print_seqspec_html(spec)
        except Exception as exc:  # pragma: no cover - surfaced in tests
            errors.append(f"failed to render HTML for {canonical_path}: {exc}")
        else:
            if "seqspec" not in html:
                errors.append(f"unexpected HTML output for {canonical_path}")

        if assay["status"] == "validated":
            diagnostics = seqspec_check(spec)
            if diagnostics:
                errors.append(
                    f"validated assay does not pass seqspec check: {canonical_path}"
                )

        assay_html_path = paths.site_dir / assay["html_path"]
        if not assay_html_path.exists():
            errors.append(f"missing assay HTML page: {assay_html_path}")

    for page_name in ("index.html", "assays.html", "reads.html", "regions.html"):
        page_path = paths.site_dir / page_name
        if not page_path.exists():
            errors.append(f"missing site page: {page_path}")

    for forbidden in paths.docs_examples.rglob("*"):
        if forbidden.name in {".git", ".DS_Store"}:
            errors.append(f"forbidden path remains in examples tree: {forbidden}")

    return errors


def ensure_example_directories(paths: ExamplePaths) -> None:
    """Create the directory layout used by the consolidated examples tree."""
    for directory in (
        paths.docs_examples,
        paths.assays_dir,
        paths.reads_dir,
        paths.regions_dir,
        paths.site_dir,
        paths.site_assays_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def normalize_canonical_examples(paths: ExamplePaths) -> None:
    """Normalize the maintained assay, read, and region examples in place."""
    for assay_path in sorted(paths.assays_dir.glob("*.yaml")):
        assay = safe_load_strip_tags(assay_path)
        normalized = normalize_assay_dict(assay, canonical=True)
        write_yaml(assay_path, normalized)

    for read_path in sorted(paths.reads_dir.glob("*.yaml")):
        read_data = safe_load_strip_tags(read_path)
        normalized = normalize_read_template(read_data)
        write_yaml(read_path, normalized)

    for region_path in sorted(paths.regions_dir.glob("*.yaml")):
        region_data = safe_load_strip_tags(region_path)
        normalized = normalize_region_template(region_data)
        write_yaml(region_path, normalized)


def build_manifest(paths: ExamplePaths) -> dict[str, Any]:
    """Build the manifest that drives validation and site generation."""
    assays: list[dict[str, Any]] = []

    for assay_path in sorted(paths.assays_dir.glob("*.yaml")):
        spec = load_spec(assay_path, strict=False)
        slug = assay_path.name.removesuffix(".spec.yaml")
        try:
            diagnostics = seqspec_check(spec)
        except Exception as exc:
            diagnostics = [
                {
                    "severity": "error",
                    "error_type": "manifest_check",
                    "error_message": str(exc),
                    "error_object": assay_path.name,
                }
            ]
        status = assay_status(slug, diagnostics)
        assays.append(
            {
                "slug": slug,
                "name": display_assay_name(spec.name, slug),
                "assay_id": text_or_empty(spec.assay_id) or slug,
                "assay_link": text_or_empty(spec.lib_struct),
                "canonical_path": str(Path("assays") / assay_path.name),
                "sequence_protocol": display_sequence_protocol(spec.sequence_protocol),
                "date": text_or_empty(spec.date),
                "status": status,
                "modalities": list(spec.modalities),
                "notes": assay_notes(status, diagnostics),
                "html_path": str(Path("assays") / f"{slug}.html"),
            }
        )

    return {
        "manifest_version": MANIFEST_VERSION,
        "assays": assays,
    }


def assay_status(slug: str, diagnostics: list[dict[str, Any]]) -> str:
    """Choose the manifest status for one maintained assay example."""
    if slug == "template":
        return "template"
    if not diagnostics:
        return "validated"
    return "example"


def assay_notes(status: str, diagnostics: list[dict[str, Any]]) -> str:
    """Write one short note for an assay manifest entry."""
    if status == "template":
        return "Structure template with intentionally incomplete metadata."
    if status == "validated":
        return "Current 0.4.0 example that passes seqspec check."
    if any(d["error_type"] == "check_schema" for d in diagnostics):
        return "Current 0.4.0 example with intentionally incomplete local metadata."
    return "Current 0.4.0 example that loads and renders but is not fully check-clean."


def write_examples_readme(paths: ExamplePaths, manifest: dict[str, Any]) -> None:
    """Write the top-level README for docs/examples."""
    assays = manifest["assays"]
    templates = sum(1 for assay in assays if assay["status"] == "template")
    validated = sum(1 for assay in assays if assay["status"] == "validated")
    examples = sum(1 for assay in assays if assay["status"] == "example")

    lines = [
        "# Examples",
        "",
        "This directory holds the maintained example material for `seqspec`.",
        "It has two parts: canonical examples and a generated HTML site.",
        "",
        "## Layout",
        "",
        "- `assays/`: maintained assay examples in current `0.4.0` structure",
        "- `reads/`: maintained read templates in current structure",
        "- `regions/`: maintained region templates in current structure",
        "- `site/`: generated static HTML pages built from the maintained examples",
        "- `examples.yaml`: manifest used for validation and site generation",
        "",
        "## Status",
        "",
        f"- `{templates}` `template` assays: intentionally incomplete structure templates",
        f"- `{examples}` `example` assays: current examples that load and render but may not fully pass `seqspec check`",
        f"- `{validated}` `validated` assays: current examples that pass `seqspec check`",
        "",
        "## Regenerate",
        "",
        "Run:",
        "",
        "```bash",
        "uv run python docs/examples/build_examples.py",
        "```",
        "",
        "The script rewrites the maintained YAML, writes the manifest, and regenerates the site.",
    ]
    paths.readme_path.write_text("\n".join(lines) + "\n")


def write_site(paths: ExamplePaths, manifest: dict[str, Any]) -> None:
    """Write the generated static HTML site."""
    if paths.site_dir.exists():
        shutil.rmtree(paths.site_dir)
    paths.site_assays_dir.mkdir(parents=True, exist_ok=True)

    assays = manifest["assays"]
    write_text(paths.site_dir / "index.html", site_index_html(assays))
    write_text(paths.site_dir / "assays.html", site_assays_html(assays))
    write_text(paths.site_dir / "reads.html", site_reads_html(paths))
    write_text(paths.site_dir / "regions.html", site_regions_html(paths))

    for assay in assays:
        spec_path = paths.docs_examples / assay["canonical_path"]
        spec = load_spec(spec_path, strict=False)
        html_path = paths.site_dir / assay["html_path"]
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(print_seqspec_html(spec))


def remove_superseded_example_sources(paths: ExamplePaths) -> None:
    """Remove old source directories that were replaced by the archive tree."""
    for source in (
        paths.docs_examples / "legacy",
        paths.docs_examples / "seqspec-builder",
        paths.docs_examples / "seqspec-builder1",
        paths.docs_examples / "seqspec",
    ):
        if source.exists():
            shutil.rmtree(source)


def normalize_assay_dict(data: dict[str, Any], canonical: bool) -> dict[str, Any]:
    """Normalize one assay YAML payload."""
    assay = dict(data)
    assay["seqspec_version"] = "0.4.0"
    assay["sequence_spec"] = reconcile_read_modalities(
        normalize_sequence_spec(
            assay.get("sequence_spec", []),
            preserve_files=not canonical,
            template_reads=False,
        ),
        list(assay.get("modalities", [])),
    )
    assay["library_spec"] = [
        normalize_region_dict(region) for region in assay.get("library_spec", [])
    ]
    assay = ensure_top_level_modality_regions(assay)
    assay["sequence_spec"] = rewrite_sequence_spec_from_library(assay)
    assay["sequence_spec"] = reconcile_read_primers(assay["sequence_spec"], assay)

    return ordered_mapping(
        seqspec_version=assay.get("seqspec_version"),
        assay_id=assay.get("assay_id"),
        name=assay.get("name"),
        doi=assay.get("doi"),
        date=assay.get("date"),
        description=assay.get("description"),
        modalities=list(assay.get("modalities", [])),
        lib_struct=assay.get("lib_struct"),
        sequence_protocol=assay.get("sequence_protocol"),
        sequence_kit=assay.get("sequence_kit"),
        library_protocol=assay.get("library_protocol"),
        library_kit=assay.get("library_kit"),
        sequence_spec=assay["sequence_spec"],
        library_spec=assay["library_spec"],
    )


def ensure_top_level_modality_regions(assay: dict[str, Any]) -> dict[str, Any]:
    """Wrap old top-level region lists into one modality region when needed."""
    modalities = list(assay.get("modalities", []))
    library_spec = list(assay.get("library_spec", []))
    top_level_ids = {region.get("region_id") for region in library_spec}

    if all(modality in top_level_ids for modality in modalities):
        return assay
    if len(modalities) != 1:
        return assay

    modality = modalities[0]
    assay["library_spec"] = [
        ordered_mapping(
            region_id=modality,
            region_type=modality,
            name=assay.get("name") or modality,
            sequence_type="joined",
            sequence="".join(
                str(region.get("sequence") or "") for region in library_spec
            ),
            min_len=sum(zero_if_none(region.get("min_len")) for region in library_spec),
            max_len=sum(zero_if_none(region.get("max_len")) for region in library_spec),
            onlist=None,
            regions=library_spec,
        )
    ]
    return assay


def reconcile_read_modalities(
    reads: list[dict[str, Any]],
    modalities: list[str],
) -> list[dict[str, Any]]:
    """Rewrite obvious legacy workflow modalities onto assay modalities."""
    normalized_reads: list[dict[str, Any]] = []
    for read in reads:
        read_modality = read.get("modality")
        if read_modality in modalities:
            normalized_reads.append(read)
            continue

        inferred = infer_read_modality(read, modalities)
        if inferred:
            normalized_reads.append({**read, "modality": inferred})
            continue

        normalized_reads.append(read)
    return normalized_reads


def infer_read_modality(read: dict[str, Any], modalities: list[str]) -> str | None:
    """Infer a read modality from its ids when the file still uses an old workflow label."""
    if len(modalities) == 1:
        return modalities[0]

    probes = [
        str(read.get("read_id") or ""),
        str(read.get("primer_id") or ""),
        str(read.get("name") or ""),
    ]
    for modality in modalities:
        prefixes = (f"{modality}-", f"{modality}_", f"{modality}.")
        if any(probe.startswith(prefixes) for probe in probes):
            return modality
    return None


def rewrite_sequence_spec_from_library(assay: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive sequence_spec reads from legacy read containers when possible."""
    original_reads = list(assay.get("sequence_spec", []))
    original_lookup = build_read_lookup(original_reads)
    rewritten_reads: list[dict[str, Any]] = []

    for modality in assay.get("modalities", []):
        libspec = get_modality_libspec(assay, modality)
        if libspec is None:
            continue

        rewrite = rewrite_legacy_modality(libspec, modality, original_lookup)
        if rewrite["reads"]:
            libspec["regions"] = rewrite["regions"]
            rewritten_reads.extend(rewrite["reads"])
            continue

        rewritten_reads.extend(
            [read for read in original_reads if read.get("modality") == modality]
        )

    return rewritten_reads or original_reads


def reconcile_read_primers(
    reads: list[dict[str, Any]],
    assay: dict[str, Any],
) -> list[dict[str, Any]]:
    """Replace generic primer ids with region ids that exist in the library tree."""
    updated_reads: list[dict[str, Any]] = []
    for read in reads:
        modality = read.get("modality")
        libspec = get_modality_libspec(assay, modality)
        if libspec is None:
            updated_reads.append(read)
            continue

        leaf_ids = {leaf["region_id"] for leaf in region_leaves(libspec)}
        if read.get("primer_id") in leaf_ids:
            updated_reads.append(read)
            continue

        inferred = infer_read_anchor(read, libspec)
        if inferred is None:
            updated_reads.append(read)
            continue

        updated_reads.append(
            {
                **read,
                "primer_id": inferred["primer_id"],
                "strand": inferred["strand"],
            }
        )
    return updated_reads


def infer_read_anchor(
    read: dict[str, Any],
    libspec: dict[str, Any],
) -> dict[str, str] | None:
    """Infer the best primer region for one read from its label and the library tree."""
    anchors = {
        leaf["region_type"]: leaf["region_id"]
        for leaf in region_leaves(libspec)
        if leaf.get("region_type") in ANCHOR_REGION_TYPES
    }
    probe = f"{read.get('read_id', '')} {read.get('name', '')}"

    def choose(
        preferred_types: list[str],
        strand: str,
    ) -> dict[str, str] | None:
        for region_type in preferred_types:
            primer_id = anchors.get(region_type)
            if primer_id:
                return {"primer_id": primer_id, "strand": strand}
        return None

    if re.search(r"(?i)(i2|index\s*2|i5)", probe):
        return choose(
            ["truseq_read1", "nextera_read1", "s5", "illumina_p5"],
            "neg",
        )
    if re.search(r"(?i)(i1|index\s*1|i7)", probe):
        return choose(
            ["truseq_read2", "nextera_read2", "s7", "illumina_p7"],
            "pos",
        )
    if re.search(r"(?i)(r2|read\s*2)", probe):
        return choose(
            ["truseq_read2", "nextera_read2", "s7", "illumina_p7"],
            "neg",
        )
    if re.search(r"(?i)(r1|read\s*1)", probe):
        return choose(
            ["truseq_read1", "nextera_read1", "s5", "illumina_p5"],
            "pos",
        )
    return None


def region_leaves(region: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the leaf regions below one region tree node."""
    children = region.get("regions") or []
    if not children:
        return [region]
    leaves: list[dict[str, Any]] = []
    for child in children:
        leaves.extend(region_leaves(child))
    return leaves


def normalize_read_template(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize one read template file."""
    return ordered_mapping(
        library_protocol=data.get("library_protocol"),
        library_kit=data.get("library_kit"),
        sequence_protocol=data.get("sequence_protocol"),
        sequence_kit=data.get("sequence_kit"),
        sequence_spec=normalize_sequence_spec(
            data.get("sequence_spec", []),
            preserve_files=False,
            template_reads=True,
        ),
    )


def normalize_region_template(data: Any) -> list[dict[str, Any]]:
    """Normalize one region template file."""
    if isinstance(data, dict):
        regions = data.get("regions", [])
    else:
        regions = data or []
    return [normalize_region_dict(region) for region in regions]


def normalize_sequence_spec(
    reads: list[dict[str, Any]],
    preserve_files: bool,
    template_reads: bool,
) -> list[dict[str, Any]]:
    """Normalize a sequence_spec list."""
    normalized_reads: list[dict[str, Any]] = []
    for read in reads:
        normalized_files: list[dict[str, Any]]
        if template_reads:
            normalized_files = []
        else:
            normalized_files = normalize_file_list(
                read.get("files", []),
                keep_without_url=preserve_files,
            )
        normalized_reads.append(
            ordered_mapping(
                read_id=read.get("read_id"),
                name=read.get("name"),
                modality=read.get("modality"),
                primer_id=read.get("primer_id"),
                min_len=read.get("min_len"),
                max_len=read.get("max_len"),
                strand=read.get("strand"),
                files=normalized_files,
            )
        )
    return normalized_reads


def normalize_region_dict(region: dict[str, Any]) -> dict[str, Any]:
    """Normalize one region tree node."""
    child_regions = [
        normalize_region_dict(child) for child in (region.get("regions") or [])
    ]
    return ordered_mapping(
        region_id=region.get("region_id"),
        region_type=region.get("region_type"),
        name=region.get("name"),
        sequence_type=region.get("sequence_type"),
        sequence=region.get("sequence"),
        min_len=region.get("min_len"),
        max_len=region.get("max_len"),
        onlist=normalize_onlist(region.get("onlist")),
        regions=child_regions,
    )


def normalize_onlist(onlist: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize one onlist mapping."""
    if onlist is None:
        return None

    location = onlist.get("location")
    url = text_or_empty(onlist.get("url"))
    urltype = text_or_empty(onlist.get("urltype")) or text_or_empty(location)
    if not urltype and url:
        urltype = "http" if url.startswith(("http://", "https://")) else "local"

    return ordered_mapping(
        file_id=onlist.get("file_id"),
        filename=onlist.get("filename"),
        filetype=onlist.get("filetype", ""),
        filesize=zero_if_none(onlist.get("filesize")),
        url=url,
        urltype=urltype,
        md5=clean_md5(onlist.get("md5")),
    )


def normalize_file_list(
    files: list[dict[str, Any]],
    keep_without_url: bool,
) -> list[dict[str, Any]]:
    """Normalize one list of read files."""
    normalized: list[dict[str, Any]] = []
    for file_obj in files or []:
        file_row = normalize_file_dict(file_obj)
        if not file_row:
            continue
        if not keep_without_url and not file_row["url"]:
            continue
        normalized.append(file_row)
    return normalized


def normalize_file_dict(file_obj: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize one read file mapping."""
    url = text_or_empty(file_obj.get("url"))
    urltype = text_or_empty(file_obj.get("urltype"))
    if not urltype and url:
        urltype = "http" if url.startswith(("http://", "https://")) else "local"

    file_id = file_obj.get("file_id") or file_obj.get("filename") or url
    filename = file_obj.get("filename") or file_id
    if not file_id and not filename and not url:
        return None

    return ordered_mapping(
        file_id=file_id,
        filename=filename,
        filetype=file_obj.get("filetype", ""),
        filesize=zero_if_none(file_obj.get("filesize")),
        url=url,
        urltype=urltype,
        md5=clean_md5(file_obj.get("md5")),
    )


def rewrite_legacy_modality(
    libspec: dict[str, Any],
    modality: str,
    original_lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Rewrite one top-level modality region by extracting read containers."""
    rewritten_regions: list[dict[str, Any]] = []
    derived_reads: list[dict[str, Any]] = []
    manual_notes: list[str] = []
    children = list(libspec.get("regions", []))

    for index, child in enumerate(children):
        if not is_read_container_candidate(child):
            rewritten_regions.append(child)
            continue

        if not child.get("regions"):
            manual_notes.append(
                f"read candidate '{child.get('region_id')}' has no child regions"
            )
            rewritten_regions.append(child)
            continue

        primer = infer_primer_and_strand(children, index, child)
        if primer is None:
            manual_notes.append(
                f"could not infer primer and strand for '{child.get('region_id')}'"
            )
            rewritten_regions.append(child)
            continue

        read_id = str(child.get("region_id") or child.get("name"))
        read_name = child.get("name") or read_id
        normalized_read = ordered_mapping(
            read_id=read_id,
            name=read_name,
            modality=modality,
            primer_id=primer["primer_id"],
            min_len=child.get("min_len"),
            max_len=child.get("max_len"),
            strand=primer["strand"],
            files=lookup_existing_files(original_lookup, read_id, read_name),
        )
        derived_reads.append(normalized_read)
        rewritten_regions.extend(child.get("regions", []))

    return {
        "regions": rewritten_regions,
        "reads": derived_reads,
        "manual_notes": manual_notes,
    }


def is_read_container_candidate(region: dict[str, Any]) -> bool:
    """Return True when a legacy region is really a read container."""
    region_type = str(region.get("region_type") or "").lower()
    if region_type in {"fastq", "gz"}:
        return True
    probe = f"{region.get('region_id', '')} {region.get('name', '')}"
    return bool(READ_CONTAINER_PATTERN.search(probe))


def infer_primer_and_strand(
    siblings: list[dict[str, Any]],
    index: int,
    candidate: dict[str, Any],
) -> dict[str, str] | None:
    """Infer read anchor and strand from flanking primer-like regions."""
    prev_anchor = siblings[index - 1] if index > 0 else None
    next_anchor = siblings[index + 1] if index + 1 < len(siblings) else None

    prev_ok = prev_anchor is not None and is_anchor_region(prev_anchor)
    next_ok = next_anchor is not None and is_anchor_region(next_anchor)

    if prev_ok and not next_ok:
        return {"primer_id": prev_anchor["region_id"], "strand": "pos"}
    if next_ok and not prev_ok:
        return {"primer_id": next_anchor["region_id"], "strand": "neg"}
    if not prev_ok and not next_ok:
        return None

    hint = read_direction_hint(candidate)
    if hint == "pos":
        return {"primer_id": prev_anchor["region_id"], "strand": "pos"}
    if hint == "neg":
        return {"primer_id": next_anchor["region_id"], "strand": "neg"}
    return None


def is_anchor_region(region: dict[str, Any]) -> bool:
    """Return True if a sibling region looks like a sequencing primer anchor."""
    return str(region.get("region_type") or "") in ANCHOR_REGION_TYPES


def read_direction_hint(candidate: dict[str, Any]) -> str | None:
    """Infer read direction from the read name or id when both flanks are anchors."""
    probe = f"{candidate.get('region_id', '')} {candidate.get('name', '')}"
    if NEGATIVE_READ_HINT.search(probe):
        return "neg"
    if POSITIVE_READ_HINT.search(probe):
        return "pos"
    return None


def build_read_lookup(
    sequence_spec: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Build a lookup from read ids and names to their meaningful file lists."""
    lookup: dict[str, list[dict[str, Any]]] = {}
    for read in sequence_spec:
        files = normalize_file_list(read.get("files", []), keep_without_url=False)
        if not files:
            continue
        for key in (read.get("read_id"), read.get("name")):
            if key:
                lookup[normalize_slug(str(key))] = files
    return lookup


def lookup_existing_files(
    lookup: dict[str, list[dict[str, Any]]],
    read_id: str,
    read_name: str,
) -> list[dict[str, Any]]:
    """Look up meaningful file rows for a derived read."""
    for key in (normalize_slug(read_id), normalize_slug(read_name)):
        if key in lookup:
            return lookup[key]
    return []


def preserve_existing_reads(
    sequence_spec: list[dict[str, Any]],
    modalities: list[str],
    modality: str,
) -> list[dict[str, Any]]:
    """Preserve normalized reads when no legacy read containers were derived."""
    preserved: list[dict[str, Any]] = []
    for read in normalize_sequence_spec(
        sequence_spec,
        preserve_files=False,
        template_reads=False,
    ):
        read_modality = read.get("modality")
        if read_modality == modality:
            preserved.append(read)
            continue
        if len(modalities) == 1 and read_modality not in modalities:
            preserved.append({**read, "modality": modality})
    return preserved


def get_modality_libspec(assay: dict[str, Any], modality: str) -> dict[str, Any] | None:
    """Return the top-level library region that matches one modality."""
    for region in assay.get("library_spec", []):
        if region.get("region_id") == modality:
            return region
    return None


def ordered_mapping(**items: Any) -> dict[str, Any]:
    """Create an ordered mapping without dropping falsy but meaningful values."""
    return dict(items)


def clean_md5(value: Any) -> str:
    """Normalize placeholder md5 values."""
    if value in PLACEHOLDER_MD5_VALUES:
        return ""
    return str(value)


def text_or_empty(value: Any) -> str:
    """Normalize an optional scalar to a string."""
    if value is None:
        return ""
    return str(value)


def is_external_url(value: str) -> bool:
    """Return True when a metadata value looks like an external link."""
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def zero_if_none(value: Any) -> int:
    """Normalize an optional integer-like field."""
    if value in (None, ""):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def normalize_slug(value: str) -> str:
    """Normalize a name or path stem to a stable comparison slug."""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def write_yaml(path: Path, data: Any) -> None:
    """Write YAML with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
    )


def write_text(path: Path, text: str) -> None:
    """Write plain text to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def site_css() -> str:
    """Inline CSS used by the generated catalog pages."""
    return """
body {
  margin: 0;
  font-family: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1a1d21;
  background: #ffffff;
}
.wrap {
  max-width: 980px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}
h1, h2 {
  margin: 0 0 12px;
  font-weight: 600;
}
p {
  margin: 0 0 14px;
  line-height: 1.6;
}
.nav {
  display: flex;
  gap: 18px;
  margin: 18px 0 26px;
  font-size: 14px;
}
.nav a,
a {
  color: #1d4ed8;
  text-decoration: none;
}
.nav a:hover,
a:hover {
  text-decoration: underline;
}
.note {
  margin: 0 0 18px;
  padding: 12px 14px;
  border: 1px solid #dcdfe3;
  border-radius: 6px;
  background: #f8fafc;
}
.search {
  margin: 18px 0 20px;
}
.search input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #dcdfe3;
  border-radius: 6px;
  font: inherit;
  color: inherit;
  background: #ffffff;
}
.search input:focus {
  outline: none;
  border-color: #94a3b8;
}
.search-note {
  margin-top: 8px;
  font-size: 13px;
  color: #68707a;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th, td {
  border-bottom: 1px solid #e5e7eb;
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}
th {
  font-size: 12px;
  color: #68707a;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.mono {
  font-family: "IBM Plex Mono", Menlo, monospace;
  font-size: 12px;
}
.tag {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.tag.template { background: #f3f4f6; color: #4b5563; }
.tag.example { background: #eff6ff; color: #1d4ed8; }
.tag.validated { background: #f0fdf4; color: #166534; }
"""


def page_shell(title: str, body: str, script: str = "") -> str:
    """Wrap one catalog page in a small self-contained HTML shell."""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{escape(title)}</title>\n"
        f"  <style>{site_css()}</style>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        f"{script}\n"
        "</body>\n"
        "</html>\n"
    )


def site_nav() -> str:
    """Render the shared site navigation."""
    return (
        '<div class="nav">'
        '<a href="index.html">Overview</a>'
        '<a href="assays.html">Assays</a>'
        '<a href="reads.html">Reads</a>'
        '<a href="regions.html">Regions</a>'
        "</div>"
    )


def site_index_html(assays: list[dict[str, Any]]) -> str:
    """Render the site landing page."""
    rows = "".join(assay_catalog_rows(assays))
    body = (
        '<div class="wrap">'
        "<h1>seqspec examples</h1>"
        '<p>This site is generated from the maintained examples under <span class="mono">docs/examples</span>. '
        "It shows the current assay examples, read templates, and region templates.</p>"
        '<div class="note">'
        '<p><strong>Note.</strong> <span class="mono">seqspec</span> files are tightly tied to the data, assay design, sequencer, and library construction they describe. '
        'These examples are representative specs derived from <a href="https://teichlab.github.io/scg_lib_structs/">Teichlab library structures</a>. '
        "They are useful reference points, but they may be incomplete or incorrect for any one concrete assay or dataset that a user defines.</p>"
        "</div>"
        f"{site_nav()}"
        '<p>The assay pages below are rendered with <span class="mono">seqspec print -f seqspec-html</span>. '
        "Use the search box to filter the catalog.</p>"
        '<div class="search">'
        '<input id="assay-search" type="search" placeholder="Search name, assay, sequencer, modality, or date">'
        '<div id="assay-search-note" class="search-note">Showing all assays.</div>'
        "</div>"
        '<table id="assay-table">'
        "<thead><tr><th>Name</th><th>Assay</th><th>Sequencer</th><th>Modalities</th><th>Date</th><th>Report</th><th>seqspec</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
    )
    script = """
<script>
(function() {
  const input = document.getElementById('assay-search');
  const note = document.getElementById('assay-search-note');
  const rows = Array.from(document.querySelectorAll('#assay-table tbody .assay-row'));
  if (!input || !note || !rows.length) return;

  function render() {
    const query = input.value.trim().toLowerCase();
    let visible = 0;
    rows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      const match = !query || text.includes(query);
      row.style.display = match ? '' : 'none';
      if (match) visible += 1;
    });
    note.textContent = query
      ? `Showing ${visible} matching assay${visible === 1 ? '' : 's'}.`
      : `Showing all ${rows.length} assays.`;
  }

  input.addEventListener('input', render);
  render();
})();
</script>
"""
    return page_shell("seqspec examples", body, script)


def site_assays_html(assays: list[dict[str, Any]]) -> str:
    """Render the assay catalog page."""
    body = (
        '<div class="wrap">'
        "<h1>Assays</h1>"
        "<p>This catalog lists the maintained assay examples in current `0.4.0` structure.</p>"
        f"{site_nav()}"
        "<table>"
        "<thead><tr><th>Name</th><th>Assay</th><th>Sequencer</th><th>Modalities</th><th>Date</th><th>Report</th><th>seqspec</th></tr></thead>"
        f"<tbody>{''.join(assay_catalog_rows(assays, row_class=''))}</tbody>"
        "</table>"
        "</div>"
    )
    return page_shell("seqspec assays", body)


def assay_catalog_rows(
    assays: list[dict[str, Any]],
    row_class: str = "assay-row",
) -> list[str]:
    """Render the assay catalog rows used by the overview and assay pages."""
    rows: list[str] = []
    class_attr = f' class="{row_class}"' if row_class else ""
    for assay in assays:
        modalities = ", ".join(assay["modalities"])
        sequencer = assay["sequence_protocol"] or "\u2014"
        date = assay["date"] or "\u2014"
        assay_id = escape(assay["assay_id"])
        assay_link = assay.get("assay_link", "")
        assay_cell = (
            f'<a href="{escape(assay_link)}">{assay_id}</a>'
            if is_external_url(assay_link)
            else assay_id
        )
        rows.append(
            f"<tr{class_attr}>"
            f"<td>{escape(assay['name'])}</td>"
            f'<td class="mono">{assay_cell}</td>'
            f"<td>{escape(sequencer)}</td>"
            f"<td>{escape(modalities)}</td>"
            f"<td>{escape(date)}</td>"
            f'<td><a href="{escape(assay["html_path"])}">view</a></td>'
            f'<td><a href="../{escape(assay["canonical_path"])}">yaml</a></td>'
            "</tr>"
        )
    return rows


def site_reads_html(paths: ExamplePaths) -> str:
    """Render the read templates catalog page."""
    rows = []
    for read_path in sorted(paths.reads_dir.glob("*.yaml")):
        payload = safe_load_strip_tags(read_path)
        reads = payload.get("sequence_spec", [])
        ids = ", ".join(str(read.get("read_id")) for read in reads)
        rows.append(
            "<tr>"
            f"<td><strong>{escape(read_path.name)}</strong></td>"
            f"<td>{len(reads)}</td>"
            f'<td class="mono">{escape(ids)}</td>'
            f'<td><a href="../reads/{escape(read_path.name)}">yaml</a></td>'
            "</tr>"
        )

    body = (
        '<div class="wrap">'
        "<h1>Reads</h1>"
        "<p>This catalog lists the maintained read templates used by the assay examples.</p>"
        f"{site_nav()}"
        "<table>"
        "<thead><tr><th>Template</th><th>Reads</th><th>Read ids</th><th>Link</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
    )
    return page_shell("seqspec read templates", body)


def site_regions_html(paths: ExamplePaths) -> str:
    """Render the region templates catalog page."""
    rows = []
    for region_path in sorted(paths.regions_dir.glob("*.yaml")):
        payload = safe_load_strip_tags(region_path)
        region_ids = ", ".join(str(region.get("region_id")) for region in payload)
        rows.append(
            "<tr>"
            f"<td><strong>{escape(region_path.name)}</strong></td>"
            f"<td>{len(payload)}</td>"
            f'<td class="mono">{escape(region_ids)}</td>'
            f'<td><a href="../regions/{escape(region_path.name)}">yaml</a></td>'
            "</tr>"
        )

    body = (
        '<div class="wrap">'
        "<h1>Regions</h1>"
        "<p>This catalog lists the maintained region templates used by the assay examples.</p>"
        f"{site_nav()}"
        "<table>"
        "<thead><tr><th>Template</th><th>Regions</th><th>Region ids</th><th>Link</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
    )
    return page_shell("seqspec region templates", body)


def display_assay_name(name: Any, slug: str) -> str:
    """Choose a stable display name for one assay entry."""
    text = text_or_empty(name)
    if text and text.lower() != "example assay":
        return text
    return slug.replace("_", " ").replace("-", " ")


def display_sequence_protocol(value: Any) -> str:
    """Choose a readable sequencer label from a protocol field."""
    if value in (None, "", []):
        return ""
    if isinstance(value, list):
        labels: list[str] = []
        for item in value:
            if isinstance(item, dict):
                label = text_or_empty(item.get("name")) or text_or_empty(
                    item.get("protocol_id")
                )
            else:
                label = text_or_empty(getattr(item, "name", None)) or text_or_empty(
                    getattr(item, "protocol_id", None)
                )
            if label and label not in labels:
                labels.append(label)
        return ", ".join(labels)
    return text_or_empty(value)
