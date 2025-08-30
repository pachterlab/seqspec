use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use crate::file::File;

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Read {
    #[pyo3(get, set)] pub read_id: String,
    #[pyo3(get, set)] pub name: String,
    #[pyo3(get, set)] pub modality: String,
    #[pyo3(get, set)] pub primer_id: String,
    #[pyo3(get, set)] pub min_len: i64,
    #[pyo3(get, set)] pub max_len: i64,
    /// "pos" | "neg"
    #[pyo3(get, set)] pub strand: String,
    #[pyo3(get, set)] pub files: Vec<File>,
}

#[pymethods]
impl Read {
    #[new]
    #[pyo3(signature = (read_id, name, modality, primer_id, min_len, max_len, strand, files = Vec::new()))]
    pub fn new(
        read_id: String, name: String, modality: String, primer_id: String,
        min_len: i64, max_len: i64, strand: String, files: Vec<File>
    ) -> Self {
        Self { read_id, name, modality, primer_id, min_len, max_len, strand, files }
    }

    #[staticmethod]
    pub fn from_json(json_str: &str) -> PyResult<Self> {
        serde_json::from_str(json_str)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to parse JSON: {}", e)))
    }

    pub fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to serialize to JSON: {}", e)))
    }

    pub fn update_files(&mut self, files: Vec<File>) { self.files = files; }

    pub fn update_read_by_id(
        &mut self,
        read_id: Option<String>,
        name: Option<String>,
        modality: Option<String>,
        primer_id: Option<String>,
        min_len: Option<i64>,
        max_len: Option<i64>,
        strand: Option<String>,
        files: Option<Vec<File>>,
    ) {
        if let Some(v) = read_id { self.read_id = v; }
        if let Some(v) = name { self.name = v; }
        if let Some(v) = modality { self.modality = v; }
        if let Some(v) = primer_id { self.primer_id = v; }
        if let Some(v) = min_len { self.min_len = v; }
        if let Some(v) = max_len { self.max_len = v; }
        if let Some(v) = strand { self.strand = v; }
        if let Some(v) = files { self.files = v; }
    }

    /// Return self if any File has matching file_id, else None.
    pub fn get_read_by_file_id(&self, file_id: &str) -> Option<Self> {
        if self.files.iter().any(|f| f.file_id == file_id) {
            Some(self.clone())
        } else { None }
    }

    pub fn __repr__(&self) -> String {
        let sign = if self.strand == "pos" { "+" } else { "-" };
        format!("{sign}({}, {}){}:{}", self.min_len, self.max_len, self.read_id, self.primer_id)
    }
}