use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::fmt;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct RegionType(pub String);

impl RegionType {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl From<&str> for RegionType {
    fn from(value: &str) -> Self {
        Self(value.to_string())
    }
}

impl From<String> for RegionType {
    fn from(value: String) -> Self {
        Self(value)
    }
}

impl fmt::Display for RegionType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[serde(untagged)]
pub enum RegionTypeValue {
    Single(RegionType),
    Multiple(Vec<RegionType>),
}

impl RegionTypeValue {
    pub fn values(&self) -> Vec<&str> {
        match self {
            RegionTypeValue::Single(value) => vec![value.as_str()],
            RegionTypeValue::Multiple(values) => values.iter().map(|v| v.as_str()).collect(),
        }
    }

    pub fn display(&self) -> String {
        self.values().join("+")
    }

    pub fn to_uppercase(&self) -> String {
        self.display().to_uppercase()
    }

    pub fn to_lowercase(&self) -> String {
        self.display().to_lowercase()
    }

    pub fn terms(&self) -> BTreeSet<String> {
        let mut terms = BTreeSet::new();
        for value in self.values() {
            for term in normalize_region_type_value(value) {
                terms.insert(term.to_string());
            }
        }
        terms
    }

    pub fn matches(&self, query: &str) -> bool {
        if self.values().iter().any(|value| *value == query) {
            return true;
        }
        let query_terms: BTreeSet<String> = normalize_region_type_value(query)
            .into_iter()
            .map(|term| term.to_string())
            .collect();
        self.terms().iter().any(|term| query_terms.contains(term))
    }

    pub fn has_term(&self, term: &str) -> bool {
        self.terms().contains(term)
    }

    pub fn has_all_terms(&self, terms: &[&str]) -> bool {
        let current = self.terms();
        terms.iter().all(|term| current.contains(*term))
    }

    pub fn upgraded_terms(&self) -> Vec<String> {
        let mut out: Vec<String> = Vec::new();
        let mut seen: BTreeSet<String> = BTreeSet::new();
        for value in self.values() {
            let mut mapped = normalize_region_type_value(value);
            if mapped.len() == 1 && mapped[0] == value && !is_ontology_term(value) {
                mapped = vec![UNKNOWN_REGION_TYPE.to_string()];
            }
            for term in mapped {
                if seen.insert(term.to_string()) {
                    out.push(term.to_string());
                }
            }
        }
        out
    }
}

impl From<&str> for RegionTypeValue {
    fn from(value: &str) -> Self {
        Self::Single(RegionType::from(value))
    }
}

impl From<String> for RegionTypeValue {
    fn from(value: String) -> Self {
        Self::Single(RegionType::from(value))
    }
}

impl From<Vec<String>> for RegionTypeValue {
    fn from(values: Vec<String>) -> Self {
        Self::Multiple(values.into_iter().map(RegionType::from).collect())
    }
}

impl fmt::Display for RegionTypeValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.display())
    }
}

impl PartialEq<&str> for RegionTypeValue {
    fn eq(&self, other: &&str) -> bool {
        self.values().iter().any(|value| value == other)
    }
}

impl PartialEq<String> for RegionTypeValue {
    fn eq(&self, other: &String) -> bool {
        self.values().iter().any(|value| *value == other.as_str())
    }
}

pub const UNKNOWN_REGION_TYPE: &str = "RGN:unknown:unclassified";
const CELL_PARTITION_TERM: &str = "RGN:partition:cell";
const MOLECULE_PARTITION_TERM: &str = "RGN:partition:molecule";
const SAMPLE_PARTITION_TERM: &str = "RGN:partition:sample";
const TRANSCRIPT_MEASURE_TERM: &str = "RGN:measure:transcript";
const GENOME_MEASURE_TERM: &str = "RGN:measure:genome";
const CHROMATIN_ACCESSIBILITY_MEASURE_TERM: &str = "RGN:measure:chromatin_accessibility";
const GUIDE_MEASURE_TERM: &str = "RGN:measure:guide";
const PROTEIN_FEATURE_MEASURE_TERM: &str = "RGN:measure:protein_feature";
const REPORTER_MEASURE_TERM: &str = "RGN:measure:reporter";
const LINKER_TECHNICAL_TERM: &str = "RGN:technical:linker";
const INDEX5_TECHNICAL_TERM: &str = "RGN:technical:index5";
const INDEX7_TECHNICAL_TERM: &str = "RGN:technical:index7";
const FEATURE_MEASURE_TERMS: &[&str] = &[
    TRANSCRIPT_MEASURE_TERM,
    GENOME_MEASURE_TERM,
    CHROMATIN_ACCESSIBILITY_MEASURE_TERM,
    GUIDE_MEASURE_TERM,
    PROTEIN_FEATURE_MEASURE_TERM,
    REPORTER_MEASURE_TERM,
];
const TECHNICAL_SKIP_TERMS: &[&str] = &[
    "RGN:technical:adapter",
    "RGN:technical:primer",
    LINKER_TECHNICAL_TERM,
    "RGN:technical:spacer",
    "RGN:technical:template_switch",
    "RGN:technical:capture_sequence",
    "RGN:technical:scaffold",
];

impl RegionTypeValue {
    pub fn is_cell_barcode(&self) -> bool {
        self.has_term(CELL_PARTITION_TERM)
    }

    pub fn is_molecule_barcode(&self) -> bool {
        self.has_term(MOLECULE_PARTITION_TERM)
    }

    pub fn is_transcript(&self) -> bool {
        self.has_term(TRANSCRIPT_MEASURE_TERM)
    }

    pub fn is_genome(&self) -> bool {
        self.has_term(GENOME_MEASURE_TERM) || self.has_term(CHROMATIN_ACCESSIBILITY_MEASURE_TERM)
    }

    pub fn is_feature(&self) -> bool {
        FEATURE_MEASURE_TERMS.iter().any(|term| self.has_term(term))
    }

    pub fn is_linker(&self) -> bool {
        self.has_term(LINKER_TECHNICAL_TERM)
    }

    pub fn is_index5(&self) -> bool {
        self.has_all_terms(&[SAMPLE_PARTITION_TERM, INDEX5_TECHNICAL_TERM])
    }

    pub fn is_index7(&self) -> bool {
        self.has_all_terms(&[SAMPLE_PARTITION_TERM, INDEX7_TECHNICAL_TERM])
    }

    pub fn is_technical_skip(&self) -> bool {
        TECHNICAL_SKIP_TERMS.iter().any(|term| self.has_term(term))
    }

    pub fn tool_label(&self) -> String {
        if self.is_cell_barcode() {
            "barcode".to_string()
        } else if self.is_molecule_barcode() {
            "umi".to_string()
        } else if self.is_transcript() {
            "cdna".to_string()
        } else if self.is_genome() {
            "gdna".to_string()
        } else if self.has_term(PROTEIN_FEATURE_MEASURE_TERM) {
            "protein".to_string()
        } else if self.has_term(GUIDE_MEASURE_TERM) {
            "sgrna_target".to_string()
        } else if self.has_term(REPORTER_MEASURE_TERM) {
            "tag".to_string()
        } else if self.is_index5() {
            "index5".to_string()
        } else if self.is_index7() {
            "index7".to_string()
        } else if self.is_linker() {
            "linker".to_string()
        } else {
            self.display()
        }
    }
}

pub fn is_ontology_term(value: &str) -> bool {
    value.starts_with("RGN:")
}

pub fn normalize_region_type_value(value: &str) -> Vec<String> {
    fn terms(values: &[&str]) -> Vec<String> {
        values.iter().map(|value| value.to_string()).collect()
    }

    match value {
        "atac" => terms(&["RGN:measure:chromatin_accessibility"]),
        "barcode" => terms(&["RGN:partition:cell"]),
        "bead_tso" | "bead_TSO" => terms(&["RGN:technical:template_switch"]),
        "cdna" | "cDNA" => terms(&["RGN:measure:transcript"]),
        "crispr" => terms(&["RGN:measure:guide", "RGN:classify:perturbation"]),
        "custom_primer" => terms(&["RGN:technical:primer"]),
        "dna" | "gdna" | "gDNA" | "hic" | "methyl" => terms(&["RGN:measure:genome"]),
        "illumina_p5" | "illumina_p7" | "ME" | "ME1" | "ME2" | "s5" | "s7" => {
            terms(&["RGN:technical:adapter"])
        }
        "index5" => terms(&["RGN:partition:sample", "RGN:technical:index5"]),
        "index7" => terms(&["RGN:partition:sample", "RGN:technical:index7"]),
        "linker" => terms(&["RGN:technical:linker"]),
        "named" | "difference" => terms(&[UNKNOWN_REGION_TYPE]),
        "nextera_read1" | "nextera_read2" | "truseq_read1" | "truseq_read2" => {
            terms(&["RGN:technical:primer"])
        }
        "poly_A" | "polyA" | "poly_C" | "poly_G" | "poly_T" | "polyT" => {
            terms(&["RGN:technical:capture_sequence"])
        }
        "protein" => terms(&["RGN:measure:protein_feature", "RGN:classify:feature"]),
        "rna" => terms(&[UNKNOWN_REGION_TYPE]),
        "sgrna_target" => terms(&["RGN:measure:guide", "RGN:classify:perturbation"]),
        "tag" => terms(&["RGN:measure:reporter"]),
        "umi" => terms(&["RGN:partition:molecule"]),
        _ => vec![value.to_string()],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_region_type_matches_legacy_and_ontology_values() {
        let ontology = RegionTypeValue::from(vec!["RGN:partition:cell".to_string()]);
        let legacy = RegionTypeValue::from("barcode");

        assert!(ontology.matches("barcode"));
        assert!(legacy.matches("RGN:partition:cell"));
        assert!(!RegionTypeValue::from("umi").matches("barcode"));
        assert!(!RegionTypeValue::from(vec![
            "RGN:partition:sample".to_string(),
            "RGN:technical:index7".to_string(),
        ])
        .matches("barcode"));
    }

    #[test]
    fn test_region_type_upgrade_maps_unknown_legacy_to_unknown_term() {
        assert_eq!(
            RegionTypeValue::from("not_curated").upgraded_terms(),
            vec![UNKNOWN_REGION_TYPE.to_string()]
        );
        assert_eq!(
            RegionTypeValue::from("index7").upgraded_terms(),
            vec![
                "RGN:partition:sample".to_string(),
                "RGN:technical:index7".to_string()
            ]
        );
    }

    #[test]
    fn test_region_type_terms_and_tool_labels_are_semantic() {
        let region_type = RegionTypeValue::from(vec![
            "RGN:partition:sample".to_string(),
            "RGN:technical:index7".to_string(),
        ]);

        assert!(region_type.is_index7());
        assert_eq!(region_type.tool_label(), "index7");
    }

    #[test]
    fn test_region_type_semantic_predicates_accept_legacy_values() {
        assert!(RegionTypeValue::from("barcode").is_cell_barcode());
        assert!(RegionTypeValue::from("truseq_read1").is_technical_skip());
    }

    #[test]
    fn test_region_type_container_labels_do_not_gain_measure_semantics() {
        let region_type = RegionTypeValue::from("rna");

        assert_eq!(
            region_type.upgraded_terms(),
            vec![UNKNOWN_REGION_TYPE.to_string()]
        );
        assert!(!region_type.is_transcript());
        assert!(!region_type.is_feature());
    }
}
