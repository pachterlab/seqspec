from pathlib import Path

from matplotlib.figure import Figure

from seqspec.Assay import Assay
from seqspec.Read import Read
from seqspec.Region import Region
from seqspec.seqspec_print import print_library_ascii, print_seqspec_png, seqspec_print
from seqspec.seqspec_print_html import build_seqspec_view_data, print_seqspec_html
from seqspec.utils import load_spec

FIXTURE = Path("tests/fixtures/spec.yaml")


def nested_spec():
    return Assay(
        seqspec_version="0.4.0",
        assay_id="nested-assay",
        name="Nested Assay",
        doi="",
        date="2026-03-24",
        description="nested regions",
        modalities=["rna"],
        lib_struct="",
        sequence_protocol=None,
        sequence_kit=None,
        library_protocol=None,
        library_kit=None,
        sequence_spec=[
            Read(
                read_id="rna_R1",
                name="Read 1",
                modality="rna",
                primer_id="joined_block",
                min_len=2,
                max_len=2,
                strand="pos",
                files=[],
            )
        ],
        library_spec=[
            Region(
                region_id="rna",
                region_type="rna",
                name="rna",
                sequence_type="joined",
                sequence="AAATXX",
                min_len=6,
                max_len=6,
                onlist=None,
                regions=[
                    Region(
                        region_id="joined_block",
                        region_type="named",
                        name="joined block",
                        sequence_type="joined",
                        sequence="AAAT",
                        min_len=4,
                        max_len=4,
                        onlist=None,
                        regions=[
                            Region(
                                region_id="fixed_a",
                                region_type="linker",
                                name="fixed a",
                                sequence_type="fixed",
                                sequence="AAA",
                                min_len=3,
                                max_len=3,
                                onlist=None,
                                regions=[],
                            ),
                            Region(
                                region_id="fixed_t",
                                region_type="linker",
                                name="fixed t",
                                sequence_type="fixed",
                                sequence="T",
                                min_len=1,
                                max_len=1,
                                onlist=None,
                                regions=[],
                            ),
                        ],
                    ),
                    Region(
                        region_id="umi",
                        region_type="umi",
                        name="umi",
                        sequence_type="random",
                        sequence="XX",
                        min_len=2,
                        max_len=2,
                        onlist=None,
                        regions=[],
                    ),
                ],
            )
        ],
    )


def test_print_library_ascii_contains_regions():
    spec = load_spec(FIXTURE)
    rendered = print_library_ascii(spec)
    assert "rna_cell_bc" in rendered
    assert "protein_truseq_read1" in rendered
    assert "atac_cell_bc" in rendered


def test_print_seqspec_png_returns_figure():
    spec = load_spec(FIXTURE)
    figure = print_seqspec_png(spec)
    assert isinstance(figure, Figure)


def test_print_seqspec_pdf_returns_figure():
    spec = load_spec(FIXTURE)
    figure = seqspec_print(spec, "seqspec-pdf", label="region_id")
    assert isinstance(figure, Figure)


def test_print_seqspec_png_supports_label_modes():
    figure = print_seqspec_png(nested_spec(), label="name+length")
    rendered_text = {text.get_text() for ax in figure.axes for text in ax.texts}
    assert "fixed a 3" in rendered_text
    assert "fixed t 1" in rendered_text


def test_print_seqspec_png_can_hide_region_labels():
    figure = print_seqspec_png(nested_spec(), label="none")
    rendered_text = {text.get_text() for ax in figure.axes for text in ax.texts}
    assert "fixed a" not in rendered_text
    assert "fixed t" not in rendered_text


def test_build_seqspec_view_data_contains_modalities():
    spec = load_spec(FIXTURE)
    data = build_seqspec_view_data(spec)
    assert data["assay_id"] == "DOGMAseq-DIG"
    assert len(data["modalities"]) == 4
    assert any(modality["modality"] == "rna" for modality in data["modalities"])


def test_build_seqspec_view_data_projects_reads():
    spec = load_spec(FIXTURE)
    data = build_seqspec_view_data(spec)
    rna = next(modality for modality in data["modalities"] if modality["modality"] == "rna")
    read = next(read for read in rna["reads"] if read["read_id"] == "rna_R2")
    assert read["strand"] == "neg"
    assert read["start"] < read["end"]
    assert len(read["files"]) == 1


def test_print_seqspec_html_contains_embedded_payload():
    spec = load_spec(FIXTURE)
    html = print_seqspec_html(spec)
    assert "seqspec-view-data" in html
    assert "DOGMAseq-DIG" in html
    assert "region-rect" in html


def test_build_seqspec_view_data_keeps_nested_regions():
    data = build_seqspec_view_data(nested_spec())
    modality = data["modalities"][0]
    parent = next(node for node in modality["region_nodes"] if node["region_id"] == "joined_block")
    child = next(node for node in modality["region_nodes"] if node["region_id"] == "fixed_a")
    assert parent["is_leaf"] is False
    assert parent["child_region_ids"] == ["fixed_a", "fixed_t"]
    assert child["path_region_ids"] == ["joined_block", "fixed_a"]


def test_build_seqspec_view_data_projects_reads_from_parent_region():
    data = build_seqspec_view_data(nested_spec())
    read = data["modalities"][0]["reads"][0]
    assert read["primer_id"] == "joined_block"
    assert read["start"] == 4
    assert read["end"] == 6


def test_print_seqspec_html_contains_nested_region_payload():
    html = print_seqspec_html(nested_spec())
    assert "joined_block" in html
    assert "group-rect" in html
