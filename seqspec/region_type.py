"""Region type ontology helpers.

The seqspec file format accepts legacy scalar labels such as ``barcode`` and
ontology terms such as ``RGN:partition:cell``. Runtime code should normalize both
forms to ontology terms before making behavior decisions.
"""

from __future__ import annotations

from typing import Iterable, Union

from pydantic_core import core_schema


class RegionType(str):
    """String-like region type value.

    This is intentionally not a closed enum. The ontology registry can grow
    without requiring a code release, while old constants such as
    ``RegionType.BARCODE`` remain available for user code.
    """

    ATAC = "atac"
    BARCODE = "barcode"
    BEAD_TSO = "bead_TSO"
    CDNA = "cdna"
    CRISPR = "crispr"
    CUSTOM_PRIMER = "custom_primer"
    DNA = "dna"
    FASTQ = "fastq"
    FASTQ_LINK = "fastq_link"
    GDNA = "gdna"
    HIC = "hic"
    ILLUMINA_P5 = "illumina_p5"
    ILLUMINA_P7 = "illumina_p7"
    INDEX5 = "index5"
    INDEX7 = "index7"
    LINKER = "linker"
    ME1 = "ME1"
    ME2 = "ME2"
    METHYL = "methyl"
    NAMED = "named"
    NEXTERA_READ1 = "nextera_read1"
    NEXTERA_READ2 = "nextera_read2"
    POLY_A = "poly_A"
    POLY_G = "poly_G"
    POLY_T = "poly_T"
    POLY_C = "poly_C"
    PROTEIN = "protein"
    RNA = "rna"
    S5 = "s5"
    S7 = "s7"
    SGRNA_TARGET = "sgrna_target"
    TAG = "tag"
    TRUSEQ_READ1 = "truseq_read1"
    TRUSEQ_READ2 = "truseq_read2"
    UMI = "umi"
    DIFFERENCE = "difference"

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        return core_schema.no_info_after_validator_function(
            cls, core_schema.str_schema()
        )


RegionTypeValue = Union[RegionType, list[RegionType]]

UNKNOWN_REGION_TYPE = "RGN:unknown:unclassified"
CELL_PARTITION_TERM = "RGN:partition:cell"
MOLECULE_PARTITION_TERM = "RGN:partition:molecule"
SAMPLE_PARTITION_TERM = "RGN:partition:sample"
TRANSCRIPT_MEASURE_TERM = "RGN:measure:transcript"
GENOME_MEASURE_TERM = "RGN:measure:genome"
CHROMATIN_ACCESSIBILITY_MEASURE_TERM = "RGN:measure:chromatin_accessibility"
GUIDE_MEASURE_TERM = "RGN:measure:guide"
PROTEIN_FEATURE_MEASURE_TERM = "RGN:measure:protein_feature"
REPORTER_MEASURE_TERM = "RGN:measure:reporter"
LINKER_TECHNICAL_TERM = "RGN:technical:linker"
INDEX5_TECHNICAL_TERM = "RGN:technical:index5"
INDEX7_TECHNICAL_TERM = "RGN:technical:index7"

FEATURE_MEASURE_TERMS = (
    TRANSCRIPT_MEASURE_TERM,
    GENOME_MEASURE_TERM,
    CHROMATIN_ACCESSIBILITY_MEASURE_TERM,
    GUIDE_MEASURE_TERM,
    PROTEIN_FEATURE_MEASURE_TERM,
    REPORTER_MEASURE_TERM,
)

TECHNICAL_SKIP_TERMS = (
    "RGN:technical:adapter",
    "RGN:technical:primer",
    LINKER_TECHNICAL_TERM,
    "RGN:technical:spacer",
    "RGN:technical:template_switch",
    "RGN:technical:capture_sequence",
    "RGN:technical:scaffold",
)

# Deterministic legacy conversion table. Synonyms in the registry are for
# human-facing search and curation; this map controls program behavior.
LEGACY_REGION_TYPE_MAP: dict[str, list[str]] = {
    "atac": ["RGN:measure:chromatin_accessibility"],
    "barcode": ["RGN:partition:cell"],
    "bead_tso": ["RGN:technical:template_switch"],
    "bead_TSO": ["RGN:technical:template_switch"],
    "cdna": ["RGN:measure:transcript"],
    "cDNA": ["RGN:measure:transcript"],
    "crispr": ["RGN:measure:guide", "RGN:classify:perturbation"],
    "custom_primer": ["RGN:technical:primer"],
    "dna": ["RGN:measure:genome"],
    "gdna": ["RGN:measure:genome"],
    "gDNA": ["RGN:measure:genome"],
    "hic": ["RGN:measure:genome"],
    "illumina_p5": ["RGN:technical:adapter"],
    "illumina_p7": ["RGN:technical:adapter"],
    "index5": ["RGN:partition:sample", "RGN:technical:index5"],
    "index7": ["RGN:partition:sample", "RGN:technical:index7"],
    "linker": ["RGN:technical:linker"],
    "ME": ["RGN:technical:adapter"],
    "ME1": ["RGN:technical:adapter"],
    "ME2": ["RGN:technical:adapter"],
    "methyl": ["RGN:measure:genome"],
    "named": [UNKNOWN_REGION_TYPE],
    "nextera_read1": ["RGN:technical:primer"],
    "nextera_read2": ["RGN:technical:primer"],
    "poly_A": ["RGN:technical:capture_sequence"],
    "polyA": ["RGN:technical:capture_sequence"],
    "poly_C": ["RGN:technical:capture_sequence"],
    "poly_G": ["RGN:technical:capture_sequence"],
    "poly_T": ["RGN:technical:capture_sequence"],
    "polyT": ["RGN:technical:capture_sequence"],
    "protein": ["RGN:measure:protein_feature", "RGN:classify:feature"],
    "rna": [UNKNOWN_REGION_TYPE],
    "s5": ["RGN:technical:adapter"],
    "s7": ["RGN:technical:adapter"],
    "sgrna_target": ["RGN:measure:guide", "RGN:classify:perturbation"],
    "tag": ["RGN:measure:reporter"],
    "truseq_read1": ["RGN:technical:primer"],
    "truseq_read2": ["RGN:technical:primer"],
    "umi": ["RGN:partition:molecule"],
    "difference": [UNKNOWN_REGION_TYPE],
}

KNOWN_REGION_TYPE_TERMS = sorted(
    {term for terms in LEGACY_REGION_TYPE_MAP.values() for term in terms}
    | {UNKNOWN_REGION_TYPE}
)


def is_ontology_term(value: str) -> bool:
    return value.startswith("RGN:")


def region_type_values(region_type: RegionTypeValue | str | list[str]) -> list[str]:
    if isinstance(region_type, list):
        return [str(value) for value in region_type]
    return [str(region_type)]


def region_type_display(region_type: RegionTypeValue | str | list[str]) -> str:
    return "+".join(region_type_values(region_type))


def normalize_region_type_value(value: str) -> list[str]:
    if is_ontology_term(value):
        return [value]
    return LEGACY_REGION_TYPE_MAP.get(value, [value])


def region_type_terms(region_type: RegionTypeValue | str | list[str]) -> set[str]:
    terms: set[str] = set()
    for value in region_type_values(region_type):
        terms.update(normalize_region_type_value(value))
    return terms


def region_type_matches(
    region_type: RegionTypeValue | str | list[str], query: str | RegionType
) -> bool:
    query_text = str(query)
    raw_values = set(region_type_values(region_type))
    if query_text in raw_values:
        return True
    query_terms = set(normalize_region_type_value(query_text))
    return bool(region_type_terms(region_type).intersection(query_terms))


def upgrade_region_type(region_type: RegionTypeValue | str | list[str]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for value in region_type_values(region_type):
        mapped = normalize_region_type_value(value)
        if mapped == [value] and not is_ontology_term(value):
            mapped = [UNKNOWN_REGION_TYPE]
        for term in mapped:
            if term not in seen:
                terms.append(term)
                seen.add(term)
    return terms


def has_region_type_term(
    region_type: RegionTypeValue | str | list[str], term: str
) -> bool:
    return term in region_type_terms(region_type)


def has_all_region_type_terms(
    region_type: RegionTypeValue | str | list[str], terms: Iterable[str]
) -> bool:
    current = region_type_terms(region_type)
    return all(term in current for term in terms)


def is_cell_barcode(region_type: RegionTypeValue | str | list[str]) -> bool:
    return has_region_type_term(region_type, CELL_PARTITION_TERM)


def is_molecule_barcode(region_type: RegionTypeValue | str | list[str]) -> bool:
    return has_region_type_term(region_type, MOLECULE_PARTITION_TERM)


def is_transcript(region_type: RegionTypeValue | str | list[str]) -> bool:
    return has_region_type_term(region_type, TRANSCRIPT_MEASURE_TERM)


def is_genome(region_type: RegionTypeValue | str | list[str]) -> bool:
    return has_region_type_term(
        region_type, GENOME_MEASURE_TERM
    ) or has_region_type_term(region_type, CHROMATIN_ACCESSIBILITY_MEASURE_TERM)


def is_feature(region_type: RegionTypeValue | str | list[str]) -> bool:
    return any(
        has_region_type_term(region_type, term) for term in FEATURE_MEASURE_TERMS
    )


def is_linker(region_type: RegionTypeValue | str | list[str]) -> bool:
    return has_region_type_term(region_type, LINKER_TECHNICAL_TERM)


def is_index5(region_type: RegionTypeValue | str | list[str]) -> bool:
    return has_all_region_type_terms(
        region_type, (SAMPLE_PARTITION_TERM, INDEX5_TECHNICAL_TERM)
    )


def is_index7(region_type: RegionTypeValue | str | list[str]) -> bool:
    return has_all_region_type_terms(
        region_type, (SAMPLE_PARTITION_TERM, INDEX7_TECHNICAL_TERM)
    )


def is_technical_skip(region_type: RegionTypeValue | str | list[str]) -> bool:
    return any(has_region_type_term(region_type, term) for term in TECHNICAL_SKIP_TERMS)


def region_type_tool_label(region_type: RegionTypeValue | str | list[str]) -> str:
    """Return the legacy tool label implied by a region type value."""
    if is_cell_barcode(region_type):
        return "barcode"
    if is_molecule_barcode(region_type):
        return "umi"
    if is_transcript(region_type):
        return "cdna"
    if is_genome(region_type):
        return "gdna"
    if has_region_type_term(region_type, PROTEIN_FEATURE_MEASURE_TERM):
        return "protein"
    if has_region_type_term(region_type, GUIDE_MEASURE_TERM):
        return "sgrna_target"
    if has_region_type_term(region_type, REPORTER_MEASURE_TERM):
        return "tag"
    if is_index5(region_type):
        return "index5"
    if is_index7(region_type):
        return "index7"
    if is_linker(region_type):
        return "linker"
    return region_type_display(region_type)
