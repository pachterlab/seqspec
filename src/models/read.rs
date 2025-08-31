use serde::{Deserialize, Serialize};
use crate::models::file::File;
use crate::models::region::RegionCoordinate;


#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Read {
    pub read_id: String,
    pub name: String,
    pub modality: String,
    pub primer_id: String,
    pub min_len: i64,
    pub max_len: i64,
    /// "pos" | "neg"
    pub strand: String,
    pub files: Vec<File>,
}


impl Read {
    pub fn new(
        read_id: String, name: String, modality: String, primer_id: String,
        min_len: i64, max_len: i64, strand: String, files: Vec<File>
    ) -> Self {
        Self { read_id, name, modality, primer_id, min_len, max_len, strand, files }
    }

    pub fn from_json(json_str: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json_str)
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
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

    pub fn repr(&self) -> String {
        let sign = if self.strand == "pos" { "+" } else { "-" };
        format!("{sign}({}, {}){}:{}", self.min_len, self.max_len, self.read_id, self.primer_id)
    }
}


#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReadCoordinate {
    pub read: Read,
    pub rcv: Vec<RegionCoordinate>, // rcv: "read coordinate vector"
}

impl ReadCoordinate {
    pub fn new(read: Read, rcv: Vec<RegionCoordinate>) -> Self {
        Self { read, rcv }
    }
}