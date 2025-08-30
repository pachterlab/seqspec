use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

use crate::read::Read;
use crate::region::Region;

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SeqProtocol {
    #[pyo3(get, set)] pub protocol_id: String,
    #[pyo3(get, set)] pub name: String,
    #[pyo3(get, set)] pub modality: String,
}

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SeqKit {
    #[pyo3(get, set)] pub kit_id: String,
    #[pyo3(get, set)] pub name: Option<String>,
    #[pyo3(get, set)] pub modality: String,
}

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LibProtocol {
    #[pyo3(get, set)] pub protocol_id: String,
    #[pyo3(get, set)] pub name: String,
    #[pyo3(get, set)] pub modality: String,
}

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LibKit {
    #[pyo3(get, set)] pub kit_id: String,
    #[pyo3(get, set)] pub name: Option<String>,
    #[pyo3(get, set)] pub modality: String,
}

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Assay {
    #[pyo3(get, set)] pub seqspec_version: Option<String>,
    #[pyo3(get, set)] pub assay_id: String,
    #[pyo3(get, set)] pub name: String,
    #[pyo3(get, set)] pub doi: String,
    #[pyo3(get, set)] pub date: String,
    #[pyo3(get, set)] pub description: String,
    #[pyo3(get, set)] pub modalities: Vec<String>,
    #[pyo3(get, set)] pub lib_struct: String,

    // Note we don't support the string type, only the object type
    #[pyo3(get, set)] pub sequence_protocol: Option<Vec<SeqProtocol>>,
    #[pyo3(get, set)] pub sequence_kit:      Option<Vec<SeqKit>>,
    #[pyo3(get, set)] pub library_protocol:  Option<Vec<LibProtocol>>,
    #[pyo3(get, set)] pub library_kit:       Option<Vec<LibKit>>,

    #[pyo3(get, set)] pub sequence_spec: Vec<Read>,
    #[pyo3(get, set)] pub library_spec:  Vec<Region>,
}

#[pymethods]
impl Assay {
    #[new]
    #[pyo3(signature = (
        assay_id, name, doi, date, description, modalities, lib_struct,
        sequence_spec = Vec::new(), library_spec = Vec::new(),
        sequence_protocol = None, sequence_kit = None, library_protocol = None, library_kit = None,
        seqspec_version = None
    ))]
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
    #[staticmethod]
    pub fn from_json(json_str: &str) -> PyResult<Self> {
        serde_json::from_str(json_str)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to parse JSON: {e}")))
    }

    pub fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to serialize to JSON: {e}")))
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

    pub fn get_libspec(&self, modality: &str) -> PyResult<Region> {
        let idx = self.modalities.iter().position(|m| m == modality)
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("Modality '{modality}' does not exist")))?;
        let r = self.library_spec.get(idx)
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("Modality '{modality}' does not exist")))?;
        // mirror Python’s check that top-level region_id equals modality
        if r.region_id != modality {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Top-level region id '{}' does not correspond to modality '{modality}'", r.region_id
            )));
        }
        Ok(r.clone())
    }

    pub fn get_seqspec(&self, modality: &str) -> Vec<Read> {
        self.sequence_spec
            .iter()
            .filter(|r| r.modality == modality)
            .cloned()
            .collect()
    }

    pub fn get_read(&self, read_id: &str) -> PyResult<Read> {
        self.sequence_spec
            .iter()
            .find(|r| r.read_id == read_id)
            .cloned()
            .ok_or_else(|| pyo3::exceptions::PyIndexError::new_err(format!(
                "read_id {read_id} not found in reads"
            )))
    }

    /// Insert regions under the top-level region for `modality`.
    /// If `after` is Some(id), insert right after that child; else insert at index 0.
    #[pyo3(signature = (regions, modality, after=None))]
    pub fn insert_regions(
        &mut self,
        regions: Vec<Region>,
        modality: String,
        after: Option<String>,
    ) -> PyResult<()> {
        let idx = self.modalities.iter().position(|m| *m == modality)
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("Modality '{modality}' not found.")))?;
        let target = self.library_spec.get_mut(idx)
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("Modality '{modality}' not found.")))?;

        let mut insert_idx: usize = 0;
        if let Some(aid) = after {
            let pos = target.regions.iter().position(|r| r.region_id == aid)
                .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!(
                    "No region with id '{aid}' found under modality '{modality}'"
                )))?;
            insert_idx = pos + 1;
        }

        for (k, r) in regions.into_iter().enumerate() {
            target.regions.insert(insert_idx + k, r);
        }
        target.update_attr();
        Ok(())
    }

    /// Insert reads; if `after` is Some(id), insert right after that read.
    /// Otherwise insert at the beginning. Also set read.modality = modality to mirror Python.
    #[pyo3(signature = (reads, modality, after=None))]
    pub fn insert_reads(
        &mut self,
        mut reads: Vec<Read>,
        modality: String,
        after: Option<String>,
    ) -> PyResult<()> {
        // set modality on incoming reads
        for r in &mut reads {
            r.modality = modality.clone();
        }

        let mut insert_idx: usize = 0;
        if let Some(aid) = after {
            if let Some(pos) = self.sequence_spec.iter().position(|r| r.read_id == aid) {
                insert_idx = pos + 1;
            } else {
                // if 'after' not found, follow Python behavior (no error): insert at end
                insert_idx = self.sequence_spec.len();
            }
        } else {
            insert_idx = 0;
        }

        for (k, r) in reads.into_iter().enumerate() {
            self.sequence_spec.insert(insert_idx + k, r);
        }
        Ok(())
    }

    pub fn __repr__(&self) -> String {
        format!("Assay: {}  Modalities: {:?}", self.assay_id, self.modalities)
    }
}