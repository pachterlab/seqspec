use serde::{Deserialize, Serialize};

use crate::models::read::Read;
use crate::models::region::Region;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct SeqProtocol {
    pub protocol_id: String,
    pub name: String,
    pub modality: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct SeqKit {
    pub kit_id: String,
    pub name: Option<String>,
    pub modality: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct LibProtocol {
    pub protocol_id: String,
    pub name: String,
    pub modality: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct LibKit {
    pub kit_id: String,
    pub name: Option<String>,
    pub modality: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Assay {
    pub seqspec_version: Option<String>,
    pub assay_id: String,
    pub name: String,
    pub doi: String,
    pub date: String,
    pub description: String,
    pub modalities: Vec<String>,
    pub lib_struct: String,

    // Note we don't support the string type, only the object type
    pub sequence_protocol: Option<Vec<SeqProtocol>>,
    pub sequence_kit:      Option<Vec<SeqKit>>,
    pub library_protocol:  Option<Vec<LibProtocol>>,
    pub library_kit:       Option<Vec<LibKit>>,

    pub sequence_spec: Vec<Read>,
    pub library_spec:  Vec<Region>,
}

impl Assay {
    pub fn new(
        assay_id: String,
        name: String,
        doi: String,
        date: String,
        description: String,
        modalities: Vec<String>,
        lib_struct: String,
        sequence_spec: Vec<Read>,
        library_spec: Vec<Region>,
        sequence_protocol: Option<Vec<SeqProtocol>>,
        sequence_kit: Option<Vec<SeqKit>>,
        library_protocol: Option<Vec<LibProtocol>>,
        library_kit: Option<Vec<LibKit>>,
        seqspec_version: Option<String>,
    ) -> Self {
        Self {
            seqspec_version, assay_id, name, doi, date, description, modalities, lib_struct,
            sequence_protocol, sequence_kit, library_protocol, library_kit,
            sequence_spec, library_spec
        }
    }

    // JSON I/O --------------------------------------------------------
    pub fn from_json(json_str: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json_str)
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    // Core helpers ----------------------------------------------------
    pub fn update_spec(&mut self) {
        for r in &mut self.library_spec {
            r.update_attr();
        }
    }

    pub fn list_modalities(&self) -> Vec<String> {
        self.modalities.clone()
    }

    pub fn get_libspec(&self, modality: &str) -> Option<Region> {
        self.modalities.iter().position(|m| m == modality).map(|idx| self.library_spec[idx].clone())
    }

    pub fn get_seqspec(&self, modality: &str) -> Vec<Read> {
        self.sequence_spec
            .iter()
            .filter(|r| r.modality == modality)
            .cloned()
            .collect()
    }

    pub fn get_read(&self, read_id: &str) -> Option<Read> {
        self.sequence_spec
            .iter()
            .find(|r| r.read_id == read_id)
            .cloned()
    }

    /// Insert regions under the top-level region for `modality`.
    /// If `after` is Some(id), insert right after that child; else insert at index 0.
    pub fn insert_regions(
        &mut self,
        regions: Vec<Region>,
        modality: &str,
        after: Option<&str>,
    ) -> Result<(), String> {
        let idx = self
            .modalities
            .iter()
            .position(|m| m == modality)
            .ok_or_else(|| format!("Modality '{modality}' not found"))?;

        let target = self
            .library_spec
            .get_mut(idx)
            .ok_or_else(|| format!("Library spec missing at modality '{modality}'"))?;

        // Compute insertion index
        let insert_idx = match after {
            Some(aid) => target
                .regions
                .iter()
                .position(|r| r.region_id == aid)
                .map(|pos| pos + 1)
                .ok_or_else(|| format!("No region with id '{aid}' under modality '{modality}'"))?,
            None => 0,
        };

        target.regions.splice(insert_idx..insert_idx, regions);
        target.update_attr();

        Ok(())
    }

    /// Insert reads; if `after` is Some(id), insert right after that read.
    /// Otherwise insert at the beginning. Also set read.modality = modality.
    pub fn insert_reads(
        &mut self,
        mut reads: Vec<Read>,
        modality: &str,
        after: Option<&str>,
    ) -> Result<(), String> {
        // set modality on incoming reads (reuses allocation)
        let modality_owned = modality.to_owned();
        for r in &mut reads {
            r.modality.clone_from(&modality_owned);
        }

        // compute insertion index
        let insert_idx = match after {
            Some(aid) => self
                .sequence_spec
                .iter()
                .position(|r| r.read_id == aid)
                .map(|p| p + 1)                       // insert after the found read
                .unwrap_or(self.sequence_spec.len()), // if not found, append
            None => 0,                                 // insert at beginning
        };

        // insert all reads at once
        self.sequence_spec.splice(insert_idx..insert_idx, reads);

        Ok(())
    }

    pub fn __repr__(&self) -> String {
        format!("Assay: {}  Modalities: {:?}", self.assay_id, self.modalities)
    }
}