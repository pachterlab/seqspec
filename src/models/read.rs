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

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_file() -> File {
        File::new(
            "file1".into(), "R1.fq.gz".into(), "fastq".into(),
            1024, "R1.fq.gz".into(), "local".into(), "".into(),
        )
    }

    fn sample_read() -> Read {
        Read::new(
            "test_read".into(), "Test Read".into(), "rna".into(),
            "test_primer".into(), 100, 150, "pos".into(), vec![sample_file()],
        )
    }

    #[test]
    fn test_read_creation() {
        let r = sample_read();
        assert_eq!(r.read_id, "test_read");
        assert_eq!(r.name, "Test Read");
        assert_eq!(r.modality, "rna");
        assert_eq!(r.primer_id, "test_primer");
        assert_eq!(r.min_len, 100);
        assert_eq!(r.max_len, 150);
        assert_eq!(r.strand, "pos");
        assert_eq!(r.files.len(), 1);
    }

    #[test]
    fn test_read_update_files() {
        let mut r = sample_read();
        let new_files = vec![
            File::new("f2".into(), "R2.fq".into(), "fastq".into(), 0, "".into(), "local".into(), "".into()),
        ];
        r.update_files(new_files);
        assert_eq!(r.files.len(), 1);
        assert_eq!(r.files[0].file_id, "f2");
    }

    #[test]
    fn test_read_update_by_id_partial() {
        let mut r = sample_read();
        r.update_read_by_id(
            None, Some("Updated Name".into()), None, None,
            Some(200), None, None, None,
        );
        assert_eq!(r.read_id, "test_read"); // unchanged
        assert_eq!(r.name, "Updated Name");
        assert_eq!(r.min_len, 200);
        assert_eq!(r.max_len, 150); // unchanged
    }

    #[test]
    fn test_read_update_by_id_none_keeps_original() {
        let mut r = sample_read();
        r.update_read_by_id(None, None, None, None, None, None, None, None);
        assert_eq!(r.read_id, "test_read");
        assert_eq!(r.name, "Test Read");
        assert_eq!(r.modality, "rna");
    }

    #[test]
    fn test_read_get_by_file_id_found() {
        let r = sample_read();
        let result = r.get_read_by_file_id("file1");
        assert!(result.is_some());
        assert_eq!(result.unwrap().read_id, "test_read");
    }

    #[test]
    fn test_read_get_by_file_id_not_found() {
        let r = sample_read();
        assert!(r.get_read_by_file_id("nonexistent").is_none());
    }

    #[test]
    fn test_read_repr_pos() {
        let r = sample_read();
        let repr = r.repr();
        assert!(repr.starts_with("+"));
        assert!(repr.contains("test_read"));
        assert!(repr.contains("test_primer"));
        assert!(repr.contains("100"));
        assert!(repr.contains("150"));
    }

    #[test]
    fn test_read_repr_neg() {
        let mut r = sample_read();
        r.strand = "neg".into();
        let repr = r.repr();
        assert!(repr.starts_with("-"));
    }

    #[test]
    fn test_read_json_roundtrip() {
        let r = sample_read();
        let json = r.to_json().unwrap();
        let r2 = Read::from_json(&json).unwrap();
        assert_eq!(r, r2);
    }

    #[test]
    fn test_read_coordinate_creation() {
        let r = sample_read();
        let region = crate::models::region::Region::new(
            "bc".into(), "barcode".into(), "barcode".into(), "fixed".into(),
            "ATCG".into(), 4, 4, None, vec![],
        );
        let rc = crate::models::region::RegionCoordinate::new(region, 0, 4);
        let read_coord = ReadCoordinate::new(r.clone(), vec![rc]);
        assert_eq!(read_coord.read.read_id, "test_read");
        assert_eq!(read_coord.rcv.len(), 1);
    }

    #[test]
    fn test_read_real_spec_properties() {
        let spec = crate::utils::load_spec(&std::path::PathBuf::from("tests/fixtures/spec.yaml"));
        let rna_reads = spec.get_seqspec("rna");
        assert!(!rna_reads.is_empty());
        let r = &rna_reads[0];
        assert_eq!(r.modality, "rna");
        assert!(r.min_len > 0);
        assert!(r.max_len >= r.min_len);
        assert!(r.strand == "pos" || r.strand == "neg");
    }
}