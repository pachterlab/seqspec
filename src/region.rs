use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

use crate::onlist::Onlist;
use crate::types::complement_seq;

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Region {
    #[pyo3(get, set)] pub region_id: String,
    #[pyo3(get, set)] pub region_type: String,       // keep String for simplicity
    #[pyo3(get, set)] pub name: String,
    #[pyo3(get, set)] pub sequence_type: String,     // "fixed" | "random" | "onlist" | "joined"
    #[pyo3(get, set)] pub sequence: String,
    #[pyo3(get, set)] pub min_len: i64,
    #[pyo3(get, set)] pub max_len: i64,
    #[pyo3(get, set)] pub onlist: Option<Onlist>,
    #[pyo3(get, set)] pub regions: Vec<Region>,
}

#[pymethods]
impl Region {
    #[new]
    #[pyo3(signature = (region_id, region_type, name, sequence_type, sequence, min_len, max_len, onlist=None, regions=Vec::new()))]
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
    #[staticmethod]
    pub fn from_json(json_str: &str) -> PyResult<Self> {
        serde_json::from_str(json_str)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to parse JSON: {e}")))
    }
    pub fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to serialize to JSON: {e}")))
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

    #[pyo3(signature = (target_region_id, region_id=None, region_type=None, name=None, sequence_type=None, sequence=None, min_len=None, max_len=None))]
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

    pub fn __repr__(&self) -> String {
        format!("{}({}, {})", self.region_type, self.min_len, self.max_len)
    }
}
