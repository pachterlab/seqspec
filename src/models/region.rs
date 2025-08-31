use serde::{Deserialize, Serialize};

use crate::models::onlist::Onlist;
use crate::utils::complement_seq;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Region {
    pub region_id: String,
    pub region_type: String,       // keep String for simplicity
    pub name: String,
    pub sequence_type: String,     // "fixed" | "random" | "onlist" | "joined"
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
        Self { region_id, region_type, name, sequence_type, sequence, min_len, max_len, onlist, regions }
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
        if self.region_type == region_type {
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
            set.insert(r.region_type);
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
        self.region_type = region_type;
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
        region_type: Option<String>,
        name: Option<String>,
        sequence_type: Option<String>,
        sequence: Option<String>,
        min_len: Option<i64>,
        max_len: Option<i64>,
    ) {
        if self.region_id == target_region_id {
            if let Some(v) = region_id { self.region_id = v; }
            if let Some(v) = region_type { self.region_type = v; }
            if let Some(v) = name { self.name = v; }
            if let Some(v) = sequence_type { self.sequence_type = v; }
            if let Some(v) = sequence { self.sequence = v; }
            if let Some(v) = min_len { self.min_len = v; }
            if let Some(v) = max_len { self.max_len = v; }
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
        Self { region, start, stop }
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
            (self.stop, other.start)          // self .. other gap
        } else if other.stop <= self.start {
            (other.stop, self.start)          // other .. self gap
        } else if self.start == other.start && self.stop == other.stop {
            (self.start, self.stop)           // identical intervals
        } else {
            return None;                      // overlapping but not identical
        };

        let len = (new_stop - new_start) as usize; // guaranteed >= 0 here
        let seq = "X".repeat(len);

        let new_region = Region {
            region_id: format!("{} - {}", self.region.region_id, other.region.region_id),
            region_type: "difference".to_string(),
            name: format!("{} - {}", self.region.name, other.region.name),
            sequence_type: "diff".to_string(),
            sequence: seq,
            min_len: (new_stop - new_start) as i64,
            max_len: (new_stop - new_start) as i64,
            onlist: None,
            regions: Vec::new(),
        };

        Some(Self { region: new_region, start: new_start, stop: new_stop })
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
        Self { obj, fixed, rgncdiff, loc }
    }
}