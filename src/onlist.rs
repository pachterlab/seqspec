use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[pyclass(module = "seqspec._core")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Onlist {
    #[pyo3(get, set)] pub file_id: String,
    #[pyo3(get, set)] pub filename: String,
    #[pyo3(get, set)] pub filetype: String,
    #[pyo3(get, set)] pub filesize: i64,
    #[pyo3(get, set)] pub url: String,
    #[pyo3(get, set)] pub urltype: String,
    #[pyo3(get, set)] pub md5: String,
}

#[pymethods]
impl Onlist {
    #[new]
    #[pyo3(signature = (file_id, filename, filetype, filesize, url, urltype, md5))]
    pub fn new(
        file_id: String,
        filename: String,
        filetype: String,
        filesize: i64,
        url: String,
        urltype: String,
        md5: String,
    ) -> Self {
        Self { file_id, filename, filetype, filesize, url, urltype, md5 }
    }

    #[staticmethod]
    #[pyo3(signature = (json_str))]
    pub fn from_json(json_str: &str) -> PyResult<Self> {
        serde_json::from_str(json_str)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to parse JSON: {}", e)))
    }
    #[pyo3(signature = ())]
    pub fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Failed to serialize to JSON: {}", e)))
    }
}