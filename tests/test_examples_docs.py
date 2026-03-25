import yaml

from seqspec.examples_docs import example_paths, validate_examples_tree
from seqspec.seqspec_check import seqspec_check
from seqspec.utils import load_spec


def test_examples_tree_validates():
    assert validate_examples_tree() == []


def test_manifest_paths_exist():
    paths = example_paths()
    manifest = yaml.safe_load(paths.manifest_path.read_text())

    for assay in manifest["assays"]:
        canonical_path = paths.docs_examples / assay["canonical_path"]
        html_path = paths.site_dir / assay["html_path"]
        assert canonical_path.exists()
        assert html_path.exists()


def test_canonical_assays_are_current_and_load():
    paths = example_paths()
    for assay_path in sorted(paths.assays_dir.glob("*.yaml")):
        spec = load_spec(assay_path, strict=False)
        assert spec.seqspec_version == "0.4.0"


def test_validated_assays_pass_check():
    paths = example_paths()
    manifest = yaml.safe_load(paths.manifest_path.read_text())

    for assay in manifest["assays"]:
        if assay["status"] != "validated":
            continue
        spec = load_spec(paths.docs_examples / assay["canonical_path"], strict=False)
        assert seqspec_check(spec) == []


def test_no_superseded_example_sources_remain():
    paths = example_paths()
    assert not (paths.docs_examples / "legacy").exists()
    assert not (paths.docs_examples / "seqspec").exists()
    assert not (paths.docs_examples / "seqspec-builder").exists()
    assert not (paths.docs_examples / "seqspec-builder1").exists()

    forbidden = [path for path in paths.docs_examples.rglob("*") if path.name == ".git"]
    assert forbidden == []


def test_generated_site_pages_exist():
    paths = example_paths()
    for name in ("index.html", "assays.html", "reads.html", "regions.html"):
        assert (paths.site_dir / name).exists()

    assay_pages = list((paths.site_dir / "assays").glob("*.html"))
    assert assay_pages


def test_assay_catalog_links_to_assay_metadata():
    paths = example_paths()
    manifest = yaml.safe_load(paths.manifest_path.read_text())
    index_html = (paths.site_dir / "index.html").read_text()

    assay = next(item for item in manifest["assays"] if item.get("assay_link"))

    assert assay["assay_link"] in index_html
    assert f'>{assay["assay_id"]}</a>' in index_html


def test_assay_catalog_skips_invalid_metadata_links():
    paths = example_paths()
    manifest = yaml.safe_load(paths.manifest_path.read_text())
    index_html = (paths.site_dir / "index.html").read_text()

    assay = next(
        item
        for item in manifest["assays"]
        if item.get("assay_link") and not item["assay_link"].startswith("http")
    )

    assert f'href="{assay["assay_link"]}"' not in index_html
