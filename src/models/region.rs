use serde::{Deserialize, Serialize};

use crate::models::onlist::Onlist;
use crate::models::region_type::{RegionType, RegionTypeValue};
use crate::utils::complement_seq;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Region {
    pub region_id: String,
    pub region_type: RegionTypeValue,
    pub name: String,
    pub sequence_type: String, // "fixed" | "random" | "onlist" | "joined"
    pub sequence: String,
    pub min_len: i64,
    pub max_len: i64,
    pub onlist: Option<Onlist>,
    pub regions: Vec<Region>,
}

impl Region {
    pub fn new(
        region_id: String,
        region_type: String,
        name: String,
        sequence_type: String,
        sequence: String,
        min_len: i64,
        max_len: i64,
        onlist: Option<Onlist>,
        regions: Vec<Region>,
    ) -> Self {
        Self {
            region_id,
            region_type: RegionTypeValue::from(region_type),
            name,
            sequence_type,
            sequence,
            min_len,
            max_len,
            onlist,
            regions,
        }
    }

    pub fn new_with_region_type_value(
        region_id: String,
        region_type: RegionTypeValue,
        name: String,
        sequence_type: String,
        sequence: String,
        min_len: i64,
        max_len: i64,
        onlist: Option<Onlist>,
        regions: Vec<Region>,
    ) -> Self {
        Self {
            region_id,
            region_type,
            name,
            sequence_type,
            sequence,
            min_len,
            max_len,
            onlist,
            regions,
        }
    }

    // ---- JSON I/O ---------------------------------------------------
    pub fn from_json(json_str: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json_str)
    }
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    // ---- Core helpers -----------------------------------------------
    pub fn get_sequence(&self) -> String {
        if self.regions.is_empty() {
            if self.sequence.is_empty() {
                "X".repeat(self.min_len as usize)
            } else {
                self.sequence.clone()
            }
        } else {
            let mut s = String::new();
            for r in &self.regions {
                s.push_str(&r.get_sequence());
            }
            s
        }
    }

    pub fn get_len(&self) -> (i64, i64) {
        if self.regions.is_empty() {
            (self.min_len, self.max_len)
        } else {
            let mut mn = 0i64;
            let mut mx = 0i64;
            for r in &self.regions {
                let (c_min, c_max) = r.get_len();
                mn += c_min;
                mx += c_max;
            }
            (mn, mx)
        }
    }

    pub fn update_attr(&mut self) {
        for r in &mut self.regions {
            r.update_attr();
        }
        let (mn, mx) = self.get_len();
        self.min_len = mn;
        self.max_len = mx;

        self.sequence = match self.sequence_type.as_str() {
            "random" => "X".repeat(self.min_len as usize),
            "onlist" => "N".repeat(self.min_len as usize),
            _ => self.get_sequence(),
        };
    }

    // ---- Queries ----------------------------------------------------
    pub fn get_region_by_id(&self, region_id: &str) -> Vec<Region> {
        let mut found = Vec::new();
        if self.region_id == region_id {
            found.push(self.clone());
        }
        for r in &self.regions {
            found.extend(r.get_region_by_id(region_id));
        }
        found
    }

    pub fn get_region_by_region_type(&self, region_type: &str) -> Vec<Region> {
        let mut found = Vec::new();
        if self.region_type.matches(region_type) {
            found.push(self.clone());
        }
        for r in &self.regions {
            found.extend(r.get_region_by_region_type(region_type));
        }
        found
    }

    pub fn get_onlist_regions(&self) -> Vec<Region> {
        let mut found = Vec::new();
        if self.onlist.is_some() {
            found.push(self.clone());
        }
        for r in &self.regions {
            found.extend(r.get_onlist_regions());
        }
        found
    }

    pub fn get_onlist(&self) -> Option<Onlist> {
        self.onlist.clone()
    }

    pub fn get_leaves(&self) -> Vec<Region> {
        let mut leaves = Vec::new();
        if self.regions.is_empty() {
            leaves.push(self.clone());
        } else {
            for r in &self.regions {
                leaves.extend(r.get_leaves());
            }
        }
        leaves
    }

    pub fn get_leaves_with_region_id(&self, region_id: &str) -> Vec<Region> {
        let mut leaves = Vec::new();
        if self.region_id == region_id {
            // if it matches, include this node (don’t descend)
            leaves.push(self.clone());
        } else if self.regions.is_empty() {
            // if atomic, include it
            leaves.push(self.clone());
        } else {
            for r in &self.regions {
                leaves.extend(r.get_leaves_with_region_id(region_id));
            }
        }
        leaves
    }

    pub fn get_leaf_region_types(&self) -> Vec<String> {
        use std::collections::BTreeSet;
        let mut set = BTreeSet::new();
        for r in self.get_leaves() {
            for value in r.region_type.values() {
                set.insert(value.to_string());
            }
        }
        set.into_iter().collect()
    }

    pub fn to_newick(&self) -> String {
        if self.regions.is_empty() {
            format!("'{}:{}'", self.region_id, self.max_len)
        } else {
            let inner: Vec<String> = self.regions.iter().map(|r| r.to_newick()).collect();
            format!("({}){}", inner.join(","), self.region_id)
        }
    }

    // ---- Mutations --------------------------------------------------
    pub fn update_region(
        &mut self,
        region_id: String,
        region_type: String,
        name: String,
        sequence_type: String,
        sequence: String,
        min_len: i64,
        max_len: i64,
        onlist: Option<Onlist>,
    ) {
        self.region_id = region_id;
        self.region_type = RegionTypeValue::from(region_type);
        self.name = name;
        self.sequence_type = sequence_type;
        self.sequence = sequence;
        self.min_len = min_len;
        self.max_len = max_len;
        self.onlist = onlist;
    }

    pub fn update_region_by_id(
        &mut self,
        target_region_id: String,
        region_id: Option<String>,
        region_type: Option<RegionTypeValue>,
        name: Option<String>,
        sequence_type: Option<String>,
        sequence: Option<String>,
        min_len: Option<i64>,
        max_len: Option<i64>,
    ) {
        if self.region_id == target_region_id {
            if let Some(v) = region_id {
                self.region_id = v;
            }
            if let Some(v) = region_type {
                self.region_type = v;
            }
            if let Some(v) = name {
                self.name = v;
            }
            if let Some(v) = sequence_type {
                self.sequence_type = v;
            }
            if let Some(v) = sequence {
                self.sequence = v;
            }
            if let Some(v) = min_len {
                self.min_len = v;
            }
            if let Some(v) = max_len {
                self.max_len = v;
            }
            return;
        }
        for r in &mut self.regions {
            r.update_region_by_id(
                target_region_id.clone(),
                region_id.clone(),
                region_type.clone(),
                name.clone(),
                sequence_type.clone(),
                sequence.clone(),
                min_len,
                max_len,
            );
        }
    }

    pub fn reverse(&mut self) {
        if self.regions.is_empty() {
            self.sequence = self.sequence.chars().rev().collect();
        } else {
            // preserve left-to-right topology; reverse inside each child
            for r in &mut self.regions {
                r.reverse();
            }
        }
    }

    pub fn complement(&mut self) {
        if self.regions.is_empty() {
            self.sequence = complement_seq(&self.sequence);
        } else {
            for r in &mut self.regions {
                r.complement();
            }
        }
    }

    pub fn repr(&self) -> String {
        format!("{}({}, {})", self.region_type, self.min_len, self.max_len)
    }
}

/// Region + half-open coordinates [start, stop)
/// (Python: RegionCoordinate(Region) with start/stop)
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct RegionCoordinate {
    /// Flatten so JSON/YAML has Region fields at top-level (like inheritance)
    #[serde(flatten)]
    pub region: Region,
    pub start: i64,
    pub stop: i64,
}

impl RegionCoordinate {
    pub fn new(region: Region, start: i64, stop: i64) -> Self {
        Self {
            region,
            start,
            stop,
        }
    }

    pub fn repr(&self) -> String {
        format!("{}({}, {})", self.region.region_type, self.start, self.stop)
    }

    pub fn display_string(&self) -> String {
        format!(
            "RegionCoordinate {} [{}]: [{}, {})",
            self.region.name, self.region.region_type, self.start, self.stop
        )
    }

    /// Compute the "difference" interval per Python __sub__ logic.
    /// Returns a new RegionCoordinate with region_type="difference",
    /// sequence_type="diff", and sequence = "X" * len.
    pub fn difference(&self, other: &Self) -> Option<Self> {
        let (new_start, new_stop) = if self.stop <= other.start {
            (self.stop, other.start) // self .. other gap
        } else if other.stop <= self.start {
            (other.stop, self.start) // other .. self gap
        } else if self.start == other.start && self.stop == other.stop {
            (self.start, self.stop) // identical intervals
        } else {
            return None; // overlapping but not identical
        };

        let len = (new_stop - new_start) as usize; // guaranteed >= 0 here
        let seq = "X".repeat(len);

        let new_region = Region {
            region_id: format!("{} - {}", self.region.region_id, other.region.region_id),
            region_type: RegionTypeValue::Single(RegionType::from("difference")),
            name: format!("{} - {}", self.region.name, other.region.name),
            sequence_type: "diff".to_string(),
            sequence: seq,
            min_len: (new_stop - new_start) as i64,
            max_len: (new_stop - new_start) as i64,
            onlist: None,
            regions: Vec::new(),
        };

        Some(Self {
            region: new_region,
            start: new_start,
            stop: new_stop,
        })
    }
}

/// Python: RegionCoordinateDifference
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct RegionCoordinateDifference {
    pub obj: RegionCoordinate,
    pub fixed: RegionCoordinate,
    pub rgncdiff: RegionCoordinate,
    /// "", "-", or "+"
    #[serde(default)]
    pub loc: String,
}

impl RegionCoordinateDifference {
    pub fn new(obj: RegionCoordinate, fixed: RegionCoordinate, rgncdiff: RegionCoordinate) -> Self {
        let loc = if obj.stop <= fixed.start {
            "-".to_string()
        } else if obj.start >= fixed.stop {
            "+".to_string()
        } else {
            "".to_string()
        };
        Self {
            obj,
            fixed,
            rgncdiff,
            loc,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;
    use std::path::PathBuf;

    fn leaf(id: &str, seq: &str, len: i64) -> Region {
        Region::new(
            id.into(),
            "barcode".into(),
            id.into(),
            "fixed".into(),
            seq.into(),
            len,
            len,
            None,
            vec![],
        )
    }

    fn joined(id: &str, children: Vec<Region>) -> Region {
        Region::new(
            id.into(),
            "joined".into(),
            id.into(),
            "joined".into(),
            "".into(),
            0,
            0,
            None,
            children,
        )
    }

    fn dogma_spec() -> crate::models::assay::Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    // ---- Creation ----

    #[test]
    fn test_region_creation() {
        let r = leaf("bc", "ATCG", 4);
        assert_eq!(r.region_id, "bc");
        assert_eq!(r.region_type, "barcode");
        assert_eq!(r.sequence_type, "fixed");
        assert_eq!(r.sequence, "ATCG");
        assert_eq!(r.min_len, 4);
        assert_eq!(r.max_len, 4);
        assert!(r.onlist.is_none());
        assert!(r.regions.is_empty());
    }

    // ---- get_sequence ----

    #[test]
    fn test_get_sequence_simple() {
        let r = leaf("bc", "ATCG", 4);
        assert_eq!(r.get_sequence(), "ATCG");
    }

    #[test]
    fn test_get_sequence_empty() {
        let r = Region::new(
            "bc".into(),
            "barcode".into(),
            "bc".into(),
            "random".into(),
            "".into(),
            8,
            8,
            None,
            vec![],
        );
        assert_eq!(r.get_sequence(), "XXXXXXXX");
    }

    #[test]
    fn test_get_sequence_nested() {
        let parent = joined("parent", vec![leaf("a", "AAAA", 4), leaf("b", "CCCC", 4)]);
        assert_eq!(parent.get_sequence(), "AAAACCCC");
    }

    // ---- get_len ----

    #[test]
    fn test_get_len_simple() {
        let r = Region::new(
            "r".into(),
            "umi".into(),
            "r".into(),
            "random".into(),
            "".into(),
            10,
            12,
            None,
            vec![],
        );
        assert_eq!(r.get_len(), (10, 12));
    }

    #[test]
    fn test_get_len_nested() {
        let parent = joined(
            "parent",
            vec![
                leaf("a", "AAAA", 4),
                Region::new(
                    "b".into(),
                    "umi".into(),
                    "b".into(),
                    "random".into(),
                    "".into(),
                    10,
                    12,
                    None,
                    vec![],
                ),
            ],
        );
        assert_eq!(parent.get_len(), (14, 16));
    }

    // ---- update_attr ----

    #[test]
    fn test_update_attr_fixed() {
        let mut parent = joined("parent", vec![leaf("a", "AAAA", 4), leaf("b", "CCCC", 4)]);
        parent.update_attr();
        assert_eq!(parent.min_len, 8);
        assert_eq!(parent.max_len, 8);
        assert_eq!(parent.sequence, "AAAACCCC");
    }

    #[test]
    fn test_update_attr_random() {
        let mut r = Region::new(
            "r".into(),
            "umi".into(),
            "r".into(),
            "random".into(),
            "".into(),
            10,
            10,
            None,
            vec![],
        );
        r.update_attr();
        assert_eq!(r.sequence, "XXXXXXXXXX");
    }

    #[test]
    fn test_update_attr_onlist() {
        let onlist = Onlist::new(
            "ol".into(),
            "list.txt".into(),
            "txt".into(),
            0,
            "list.txt".into(),
            "local".into(),
            "".into(),
        );
        let mut r = Region::new(
            "r".into(),
            "barcode".into(),
            "r".into(),
            "onlist".into(),
            "".into(),
            16,
            16,
            Some(onlist),
            vec![],
        );
        r.update_attr();
        assert_eq!(r.sequence, "NNNNNNNNNNNNNNNN");
        assert_eq!(r.sequence.len(), 16);
    }

    // ---- Queries ----

    #[test]
    fn test_get_region_by_id() {
        let parent = joined(
            "parent",
            vec![leaf("target", "ATCG", 4), leaf("other", "GGGG", 4)],
        );
        let found = parent.get_region_by_id("target");
        assert_eq!(found.len(), 1);
        assert_eq!(found[0].region_id, "target");
    }

    #[test]
    fn test_get_region_by_id_not_found() {
        let r = leaf("bc", "ATCG", 4);
        assert!(r.get_region_by_id("missing").is_empty());
    }

    #[test]
    fn test_get_region_by_region_type() {
        let parent = joined(
            "parent",
            vec![
                leaf("a", "AAAA", 4),
                Region::new(
                    "u".into(),
                    "umi".into(),
                    "u".into(),
                    "random".into(),
                    "".into(),
                    10,
                    10,
                    None,
                    vec![],
                ),
            ],
        );
        let barcodes = parent.get_region_by_region_type("barcode");
        assert_eq!(barcodes.len(), 1);
        assert_eq!(barcodes[0].region_id, "a");

        let umis = parent.get_region_by_region_type("umi");
        assert_eq!(umis.len(), 1);
    }

    #[test]
    fn test_get_onlist_regions() {
        let onlist = Onlist::new(
            "ol".into(),
            "list.txt".into(),
            "txt".into(),
            0,
            "".into(),
            "local".into(),
            "".into(),
        );
        let parent = joined(
            "parent",
            vec![
                Region::new(
                    "bc".into(),
                    "barcode".into(),
                    "bc".into(),
                    "onlist".into(),
                    "".into(),
                    16,
                    16,
                    Some(onlist),
                    vec![],
                ),
                leaf("other", "AAAA", 4),
            ],
        );
        let onlist_regions = parent.get_onlist_regions();
        assert_eq!(onlist_regions.len(), 1);
        assert_eq!(onlist_regions[0].region_id, "bc");
    }

    #[test]
    fn test_get_onlist() {
        let r = leaf("bc", "ATCG", 4);
        assert!(r.get_onlist().is_none());

        let onlist = Onlist::new(
            "ol".into(),
            "list.txt".into(),
            "txt".into(),
            0,
            "".into(),
            "local".into(),
            "".into(),
        );
        let r2 = Region::new(
            "bc".into(),
            "barcode".into(),
            "bc".into(),
            "onlist".into(),
            "".into(),
            16,
            16,
            Some(onlist.clone()),
            vec![],
        );
        assert_eq!(r2.get_onlist().unwrap(), onlist);
    }

    #[test]
    fn test_get_leaves() {
        let parent = joined(
            "parent",
            vec![
                leaf("a", "AAAA", 4),
                joined("inner", vec![leaf("b", "CCCC", 4), leaf("c", "GGGG", 4)]),
            ],
        );
        let leaves = parent.get_leaves();
        assert_eq!(leaves.len(), 3);
        assert_eq!(leaves[0].region_id, "a");
        assert_eq!(leaves[1].region_id, "b");
        assert_eq!(leaves[2].region_id, "c");
    }

    #[test]
    fn test_get_leaves_with_region_id() {
        let parent = joined(
            "parent",
            vec![
                leaf("a", "AAAA", 4),
                joined("inner", vec![leaf("b", "CCCC", 4), leaf("c", "GGGG", 4)]),
            ],
        );
        // Stops at "inner" and includes it instead of descending
        let leaves = parent.get_leaves_with_region_id("inner");
        assert_eq!(leaves.len(), 2);
        assert_eq!(leaves[0].region_id, "a");
        assert_eq!(leaves[1].region_id, "inner");
    }

    #[test]
    fn test_get_leaf_region_types() {
        let parent = joined(
            "parent",
            vec![
                leaf("a", "AAAA", 4), // barcode
                Region::new(
                    "u".into(),
                    "umi".into(),
                    "u".into(),
                    "random".into(),
                    "".into(),
                    10,
                    10,
                    None,
                    vec![],
                ),
                leaf("b", "CCCC", 4), // barcode
            ],
        );
        let types = parent.get_leaf_region_types();
        assert_eq!(types, vec!["barcode", "umi"]);
    }

    // ---- Newick ----

    #[test]
    fn test_to_newick_leaf() {
        let r = Region::new(
            "bc".into(),
            "barcode".into(),
            "bc".into(),
            "fixed".into(),
            "ATCG".into(),
            4,
            4,
            None,
            vec![],
        );
        assert_eq!(r.to_newick(), "'bc:4'");
    }

    #[test]
    fn test_to_newick_nested() {
        let parent = joined("parent", vec![leaf("a", "AAAA", 4), leaf("b", "CCCC", 4)]);
        assert_eq!(parent.to_newick(), "('a:4','b:4')parent");
    }

    // ---- Mutations ----

    #[test]
    fn test_reverse_leaf() {
        let mut r = leaf("bc", "ATCG", 4);
        r.reverse();
        assert_eq!(r.sequence, "GCTA");
    }

    #[test]
    fn test_reverse_nested() {
        let mut parent = joined("parent", vec![leaf("a", "ATCG", 4), leaf("b", "GGCC", 4)]);
        parent.reverse();
        assert_eq!(parent.regions[0].sequence, "GCTA");
        assert_eq!(parent.regions[1].sequence, "CCGG");
    }

    #[test]
    fn test_complement_leaf() {
        let mut r = leaf("bc", "ATCG", 4);
        r.complement();
        assert_eq!(r.sequence, "TAGC");
    }

    #[test]
    fn test_complement_nested() {
        let mut parent = joined("parent", vec![leaf("a", "ATCG", 4), leaf("b", "AAAA", 4)]);
        parent.complement();
        assert_eq!(parent.regions[0].sequence, "TAGC");
        assert_eq!(parent.regions[1].sequence, "TTTT");
    }

    #[test]
    fn test_update_region() {
        let mut r = leaf("old", "ATCG", 4);
        r.update_region(
            "new".into(),
            "umi".into(),
            "New Name".into(),
            "random".into(),
            "XXXX".into(),
            4,
            4,
            None,
        );
        assert_eq!(r.region_id, "new");
        assert_eq!(r.region_type, "umi");
        assert_eq!(r.name, "New Name");
        assert_eq!(r.sequence_type, "random");
        assert_eq!(r.sequence, "XXXX");
    }

    #[test]
    fn test_update_region_by_id() {
        let mut parent = joined(
            "parent",
            vec![leaf("target", "ATCG", 4), leaf("other", "GGGG", 4)],
        );
        parent.update_region_by_id(
            "target".into(),
            None,
            None,
            Some("Updated Name".into()),
            None,
            Some("CCCC".into()),
            None,
            None,
        );
        assert_eq!(parent.regions[0].region_id, "target"); // unchanged
        assert_eq!(parent.regions[0].name, "Updated Name");
        assert_eq!(parent.regions[0].sequence, "CCCC");
    }

    #[test]
    fn test_update_region_by_id_none_keeps_original() {
        let mut r = leaf("bc", "ATCG", 4);
        r.update_region_by_id("bc".into(), None, None, None, None, None, None, None);
        assert_eq!(r.region_id, "bc");
        assert_eq!(r.name, "bc");
        assert_eq!(r.sequence, "ATCG");
    }

    #[test]
    fn test_region_repr() {
        let r = Region::new(
            "bc".into(),
            "barcode".into(),
            "bc".into(),
            "fixed".into(),
            "ATCG".into(),
            16,
            16,
            None,
            vec![],
        );
        assert_eq!(r.repr(), "barcode(16, 16)");
    }

    #[test]
    fn test_region_json_roundtrip() {
        let r = leaf("bc", "ATCG", 4);
        let json = r.to_json().unwrap();
        let r2 = Region::from_json(&json).unwrap();
        assert_eq!(r, r2);
    }

    // ---- RegionCoordinate ----

    #[test]
    fn test_region_coordinate_creation() {
        let r = leaf("bc", "ATCG", 4);
        let rc = RegionCoordinate::new(r.clone(), 0, 4);
        assert_eq!(rc.start, 0);
        assert_eq!(rc.stop, 4);
        assert_eq!(rc.region.region_id, "bc");
    }

    #[test]
    fn test_region_coordinate_repr() {
        let r = leaf("bc", "ATCG", 4);
        let rc = RegionCoordinate::new(r, 10, 20);
        assert_eq!(rc.repr(), "barcode(10, 20)");
    }

    #[test]
    fn test_region_coordinate_difference_gap() {
        let r1 = leaf("a", "AAAA", 4);
        let r2 = leaf("b", "CCCC", 4);
        let rc1 = RegionCoordinate::new(r1, 0, 4);
        let rc2 = RegionCoordinate::new(r2, 10, 14);

        let diff = rc1.difference(&rc2).unwrap();
        assert_eq!(diff.start, 4);
        assert_eq!(diff.stop, 10);
        assert_eq!(diff.region.region_type, "difference");
        assert_eq!(diff.region.sequence, "XXXXXX");
    }

    #[test]
    fn test_region_coordinate_difference_identical() {
        let r1 = leaf("a", "AAAA", 4);
        let r2 = leaf("b", "CCCC", 4);
        let rc1 = RegionCoordinate::new(r1, 5, 10);
        let rc2 = RegionCoordinate::new(r2, 5, 10);

        let diff = rc1.difference(&rc2).unwrap();
        assert_eq!(diff.start, 5);
        assert_eq!(diff.stop, 10);
    }

    #[test]
    fn test_region_coordinate_difference_overlap_returns_none() {
        let r1 = leaf("a", "AAAA", 4);
        let r2 = leaf("b", "CCCC", 4);
        let rc1 = RegionCoordinate::new(r1, 0, 10);
        let rc2 = RegionCoordinate::new(r2, 5, 15);

        assert!(rc1.difference(&rc2).is_none());
    }

    #[test]
    fn test_region_coordinate_difference_loc() {
        let r1 = leaf("a", "AAAA", 4);
        let r2 = leaf("b", "CCCC", 4);
        let r3 = leaf("d", "XXXX", 4);

        let obj = RegionCoordinate::new(r1.clone(), 0, 4);
        let fixed = RegionCoordinate::new(r2, 10, 14);
        let rgncdiff = RegionCoordinate::new(r3, 4, 10);

        let diff = RegionCoordinateDifference::new(obj, fixed.clone(), rgncdiff);
        assert_eq!(diff.loc, "-"); // obj.stop <= fixed.start

        let obj2 = RegionCoordinate::new(r1, 20, 24);
        let r4 = leaf("e", "YYYY", 4);
        let rgncdiff2 = RegionCoordinate::new(r4, 14, 20);
        let diff2 = RegionCoordinateDifference::new(obj2, fixed, rgncdiff2);
        assert_eq!(diff2.loc, "+"); // obj.start >= fixed.stop
    }

    // ---- Real spec tests ----

    #[test]
    fn test_get_sequence_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let seq = rna_lib.get_sequence();
        assert_eq!(seq.len(), 197);
        assert!(seq.starts_with("ACACTCTTTCCCTACACGACGCTCTTCCGATCT"));
        assert!(seq.ends_with("AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC"));
        // middle contains N (barcode) and X (UMI/cDNA)
        assert!(seq.contains('N'));
        assert!(seq.contains('X'));
    }

    #[test]
    fn test_get_len_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let (mn, mx) = rna_lib.get_len();
        assert_eq!(mn, 197);
        assert_eq!(mx, 197);
    }

    #[test]
    fn test_get_region_by_id_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let found = rna_lib.get_region_by_id("rna_cell_bc");
        assert_eq!(found.len(), 1);
        assert_eq!(found[0].region_id, "rna_cell_bc");
        assert_eq!(found[0].region_type, "barcode");
        assert_eq!(found[0].min_len, 16);
        assert_eq!(found[0].max_len, 16);
        assert_eq!(found[0].sequence, "NNNNNNNNNNNNNNNN");
    }

    #[test]
    fn test_get_region_by_type_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let barcodes = rna_lib.get_region_by_region_type("barcode");
        assert_eq!(barcodes.len(), 1);
        assert_eq!(barcodes[0].region_id, "rna_cell_bc");
    }

    #[test]
    fn test_get_onlist_regions_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let onlists = rna_lib.get_onlist_regions();
        assert_eq!(onlists.len(), 1);
        assert_eq!(onlists[0].region_id, "rna_cell_bc");
    }

    #[test]
    fn test_get_leaves_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let leaves = rna_lib.get_leaves();
        assert_eq!(leaves.len(), 5);
        let leaf_ids: Vec<&str> = leaves.iter().map(|l| l.region_id.as_str()).collect();
        assert_eq!(
            leaf_ids,
            vec![
                "rna_truseq_read1",
                "rna_cell_bc",
                "rna_umi",
                "cdna",
                "rna_truseq_read2"
            ]
        );
    }

    #[test]
    fn test_get_leaf_region_types_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let types = rna_lib.get_leaf_region_types();
        // Returns sorted via BTreeSet
        assert_eq!(
            types,
            vec!["barcode", "cdna", "truseq_read1", "truseq_read2", "umi"]
        );
    }

    #[test]
    fn test_to_newick_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let newick = rna_lib.to_newick();
        assert_eq!(
            newick,
            "('rna_truseq_read1:33','rna_cell_bc:16','rna_umi:12','cdna:102','rna_truseq_read2:34')rna"
        );
    }

    #[test]
    fn test_update_attr_real_spec() {
        let spec = dogma_spec();
        let mut rna_lib = spec.get_libspec("rna").expect("rna modality").clone();
        let (mn_before, mx_before) = rna_lib.get_len();
        rna_lib.update_attr();
        // After update_attr, min/max should match computed values
        assert_eq!(rna_lib.min_len, mn_before);
        assert_eq!(rna_lib.max_len, mx_before);
        assert_eq!(rna_lib.min_len, 197);
        assert_eq!(rna_lib.max_len, 197);
        assert_eq!(rna_lib.sequence_type, "joined");
    }

    #[test]
    fn test_reverse_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        // Get a leaf with a known sequence
        let read1 = rna_lib.get_region_by_id("rna_truseq_read1");
        assert_eq!(read1.len(), 1);
        let mut r = read1[0].clone();
        let orig_seq = r.sequence.clone();
        assert_eq!(orig_seq, "ACACTCTTTCCCTACACGACGCTCTTCCGATCT");
        r.reverse();
        let expected: String = orig_seq.chars().rev().collect();
        assert_eq!(r.sequence, expected);
        assert_eq!(r.sequence, "TCTAGCCTTCTCGCAGCACATCCCTTTCTCACA");
    }

    #[test]
    fn test_complement_real_spec() {
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let read1 = rna_lib.get_region_by_id("rna_truseq_read1");
        assert_eq!(read1.len(), 1);
        let mut r = read1[0].clone();
        assert_eq!(r.sequence, "ACACTCTTTCCCTACACGACGCTCTTCCGATCT");
        r.complement();
        assert_eq!(r.sequence, "TGTGAGAAAGGGATGTGCTGCGAGAAGGCTAGA");
    }

    #[test]
    fn test_reverse_complement_barcode() {
        // Barcode with all N's: reverse and complement should both be N's
        let spec = dogma_spec();
        let rna_lib = spec.get_libspec("rna").expect("rna modality");
        let bc = rna_lib.get_region_by_id("rna_cell_bc");
        assert_eq!(bc.len(), 1);

        let mut r = bc[0].clone();
        assert_eq!(r.sequence, "NNNNNNNNNNNNNNNN");
        r.reverse();
        assert_eq!(r.sequence, "NNNNNNNNNNNNNNNN");

        let mut r2 = bc[0].clone();
        r2.complement();
        assert_eq!(r2.sequence, "NNNNNNNNNNNNNNNN");
    }
}
