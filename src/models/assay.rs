use serde::{Deserialize, Serialize};

use crate::models::file::File;
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

    pub fn to_bytes(&self) -> Result<Vec<u8>,  std::io::Error> {
        Ok(serde_yaml::to_string(self).unwrap().into_bytes())
    }
    pub fn from_bytes(bytes: &[u8]) -> Result<Self,  std::io::Error> {
        Ok(serde_yaml::from_slice(bytes).unwrap())
    }

    // Core helpers ----------------------------------------------------
    pub fn update_spec(&mut self) -> () {
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

    /// Returns the common file count if all reads have the same, non-zero length.
    fn file_count(reads: &[Read]) -> Option<usize> {
        let first = reads.first()?.files.len();
        if first == 0 { return None; }
        if reads.iter().all(|r| r.files.len() == first) { Some(first) } else { None }
    }

    pub fn generate_group_ids(&self, modality: &str) -> Vec<usize> {
        let reads = self.get_seqspec(modality);
        let n = match Self::file_count(&reads) { Some(n) => n, None => return vec![] };
        (0..n).collect()
    }

    pub fn get_read_by_group_id(&self, modality: &str, group_id: usize) -> Option<String> {
        let reads = self.get_seqspec(modality);
        let n_files = Self::file_count(&reads)?;
        if reads.is_empty() {
            return None;
        }
        let read_idx = group_id % reads.len();
        reads.get(read_idx).map(|r| r.read_id.clone())
    }

    pub fn get_files_by_group_id(&self, modality: &str, group_id: usize) -> Option<Vec<File>> {
        let reads = self.get_seqspec(modality);
        let n_files = Self::file_count(&reads)?;
        if reads.is_empty() {
            return None;
        }
        let read_idx = group_id % reads.len();
        reads.get(read_idx).map(|r| r.files.clone())
    }

}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::load_spec;
    use std::path::PathBuf;

    fn sample_file() -> File {
        File::new(
            "f1".into(), "R1.fq.gz".into(), "fastq".into(),
            1024, "R1.fq.gz".into(), "local".into(), "".into(),
        )
    }

    fn sample_read(id: &str, modality: &str) -> Read {
        Read::new(
            id.into(), id.into(), modality.into(), "primer1".into(),
            100, 150, "pos".into(), vec![sample_file()],
        )
    }

    fn sample_region(id: &str) -> Region {
        Region::new(
            id.into(), "barcode".into(), id.into(), "fixed".into(),
            "ATCG".into(), 4, 4, None, vec![],
        )
    }

    fn sample_assay() -> Assay {
        Assay::new(
            "test_assay".into(),
            "Test Assay".into(),
            "https://doi.org/test".into(),
            "20240101".into(),
            "Test description".into(),
            vec!["rna".into()],
            "".into(),
            vec![sample_read("R1", "rna"), sample_read("R2", "rna")],
            vec![Region::new(
                "rna".into(), "rna".into(), "rna".into(), "joined".into(),
                "".into(), 0, 0, None,
                vec![
                    Region::new(
                        "primer1".into(), "truseq_read1".into(), "primer1".into(),
                        "fixed".into(), "".into(), 0, 0, None, vec![],
                    ),
                    sample_region("bc"),
                    sample_region("umi"),
                ],
            )],
            None, None, None, None,
            Some("0.3.0".into()),
        )
    }

    fn dogma_spec() -> Assay {
        load_spec(&PathBuf::from("tests/fixtures/spec.yaml"))
    }

    // ---- Creation & serialization ----

    #[test]
    fn test_assay_creation() {
        let a = sample_assay();
        assert_eq!(a.assay_id, "test_assay");
        assert_eq!(a.name, "Test Assay");
        assert_eq!(a.modalities, vec!["rna"]);
        assert_eq!(a.sequence_spec.len(), 2);
        assert_eq!(a.library_spec.len(), 1);
    }

    #[test]
    fn test_assay_list_modalities() {
        let a = sample_assay();
        assert_eq!(a.list_modalities(), vec!["rna"]);
    }

    #[test]
    fn test_assay_get_libspec() {
        let a = sample_assay();
        let lib = a.get_libspec("rna");
        assert!(lib.is_some());
        assert_eq!(lib.unwrap().region_id, "rna");
    }

    #[test]
    fn test_assay_get_libspec_not_found() {
        let a = sample_assay();
        assert!(a.get_libspec("atac").is_none());
    }

    #[test]
    fn test_assay_get_seqspec() {
        let a = sample_assay();
        let reads = a.get_seqspec("rna");
        assert_eq!(reads.len(), 2);
    }

    #[test]
    fn test_assay_get_seqspec_empty() {
        let a = sample_assay();
        let reads = a.get_seqspec("unknown");
        assert!(reads.is_empty());
    }

    #[test]
    fn test_assay_get_read() {
        let a = sample_assay();
        let read = a.get_read("R1");
        assert!(read.is_some());
        assert_eq!(read.unwrap().read_id, "R1");
    }

    #[test]
    fn test_assay_get_read_not_found() {
        let a = sample_assay();
        assert!(a.get_read("nonexistent").is_none());
    }

    #[test]
    fn test_assay_update_spec() {
        let mut a = sample_assay();
        a.update_spec();
        let lib = a.get_libspec("rna").unwrap();
        assert_eq!(lib.min_len, 8); // bc(4) + umi(4) + primer(0)
        assert_eq!(lib.max_len, 8);
    }

    // ---- Insert ----

    #[test]
    fn test_assay_insert_regions() {
        let mut a = sample_assay();
        let orig_count = a.get_libspec("rna").unwrap().regions.len();
        let new_region = sample_region("new_bc");
        a.insert_regions(vec![new_region], "rna", None).unwrap();

        let lib = a.get_libspec("rna").unwrap();
        assert_eq!(lib.regions.len(), orig_count + 1);
        assert_eq!(lib.regions[0].region_id, "new_bc"); // inserted at beginning
    }

    #[test]
    fn test_assay_insert_regions_after() {
        let mut a = sample_assay();
        let new_region = sample_region("new_bc");
        a.insert_regions(vec![new_region], "rna", Some("bc")).unwrap();

        let lib = a.get_libspec("rna").unwrap();
        // Find position of new_bc — should be right after "bc"
        let bc_pos = lib.regions.iter().position(|r| r.region_id == "bc").unwrap();
        let new_pos = lib.regions.iter().position(|r| r.region_id == "new_bc").unwrap();
        assert_eq!(new_pos, bc_pos + 1);
    }

    #[test]
    fn test_assay_insert_regions_invalid_modality() {
        let mut a = sample_assay();
        let result = a.insert_regions(vec![sample_region("x")], "atac", None);
        assert!(result.is_err());
    }

    #[test]
    fn test_assay_insert_reads() {
        let mut a = sample_assay();
        let orig_count = a.sequence_spec.len();
        let new_read = Read::new(
            "I1".into(), "Index 1".into(), "".into(), "p".into(),
            8, 8, "pos".into(), vec![],
        );
        a.insert_reads(vec![new_read], "rna", None).unwrap();

        assert_eq!(a.sequence_spec.len(), orig_count + 1);
        assert_eq!(a.sequence_spec[0].read_id, "I1"); // inserted at beginning
        assert_eq!(a.sequence_spec[0].modality, "rna"); // modality set
    }

    #[test]
    fn test_assay_insert_reads_after() {
        let mut a = sample_assay();
        let new_read = Read::new(
            "I1".into(), "Index 1".into(), "".into(), "p".into(),
            8, 8, "pos".into(), vec![],
        );
        a.insert_reads(vec![new_read], "rna", Some("R1")).unwrap();

        let r1_pos = a.sequence_spec.iter().position(|r| r.read_id == "R1").unwrap();
        let i1_pos = a.sequence_spec.iter().position(|r| r.read_id == "I1").unwrap();
        assert_eq!(i1_pos, r1_pos + 1);
    }

    #[test]
    fn test_assay_json_roundtrip() {
        let a = sample_assay();
        let json = a.to_json().unwrap();
        let a2 = Assay::from_json(&json).unwrap();
        assert_eq!(a, a2);
    }

    #[test]
    fn test_assay_yaml_roundtrip() {
        let a = sample_assay();
        let bytes = a.to_bytes().unwrap();
        let a2 = Assay::from_bytes(&bytes).unwrap();
        assert_eq!(a.assay_id, a2.assay_id);
        assert_eq!(a.modalities, a2.modalities);
        assert_eq!(a.sequence_spec.len(), a2.sequence_spec.len());
    }

    #[test]
    fn test_assay_repr() {
        let a = sample_assay();
        let repr = a.__repr__();
        assert_eq!(repr, "Assay: test_assay  Modalities: [\"rna\"]");
    }

    // ---- Real spec tests ----

    #[test]
    fn test_load_dogma_spec() {
        let spec = dogma_spec();
        assert_eq!(spec.assay_id, "DOGMAseq-DIG");
    }

    #[test]
    fn test_dogma_list_modalities() {
        let spec = dogma_spec();
        let mods = spec.list_modalities();
        assert!(mods.contains(&"rna".to_string()));
        assert!(mods.contains(&"atac".to_string()));
        assert!(mods.contains(&"protein".to_string()));
        assert!(mods.contains(&"tag".to_string()));
        assert_eq!(mods.len(), 4);
    }

    #[test]
    fn test_dogma_get_libspec_rna() {
        let spec = dogma_spec();
        let lib = spec.get_libspec("rna").expect("rna modality");
        assert_eq!(lib.region_id, "rna");
    }

    #[test]
    fn test_dogma_get_seqspec_rna() {
        let spec = dogma_spec();
        let reads = spec.get_seqspec("rna");
        assert_eq!(reads.len(), 2);
        assert_eq!(reads[0].read_id, "rna_R1");
        assert_eq!(reads[1].read_id, "rna_R2");
        for r in &reads {
            assert_eq!(r.modality, "rna");
        }
    }

    #[test]
    fn test_dogma_get_read() {
        let spec = dogma_spec();
        // DOGMAseq has reads like "rna_R1", "rna_R2", "atac_R1", etc.
        // Find the first rna read
        let rna_reads = spec.get_seqspec("rna");
        assert!(!rna_reads.is_empty());
        let read_id = &rna_reads[0].read_id;
        let found = spec.get_read(read_id);
        assert!(found.is_some());
        assert_eq!(&found.unwrap().read_id, read_id);
    }

    // ---- Group ID methods ----

    #[test]
    fn test_generate_group_ids() {
        let a = sample_assay();
        let ids = a.generate_group_ids("rna");
        // Both reads have 1 file each, so group_ids = [0]
        assert_eq!(ids, vec![0]);
    }

    #[test]
    fn test_generate_group_ids_empty() {
        let a = sample_assay();
        let ids = a.generate_group_ids("nonexistent");
        assert!(ids.is_empty());
    }

    #[test]
    fn test_get_read_by_group_id() {
        let a = sample_assay();
        let read_id = a.get_read_by_group_id("rna", 0);
        assert!(read_id.is_some());
        assert_eq!(read_id.unwrap(), "R1");
    }

    #[test]
    fn test_get_read_by_group_id_wraps() {
        let a = sample_assay();
        // group_id 1 should wrap to read index 1
        let read_id = a.get_read_by_group_id("rna", 1);
        assert!(read_id.is_some());
        assert_eq!(read_id.unwrap(), "R2");
    }

    #[test]
    fn test_get_files_by_group_id() {
        let a = sample_assay();
        let files = a.get_files_by_group_id("rna", 0);
        assert!(files.is_some());
        assert_eq!(files.unwrap().len(), 1);
    }

    #[test]
    fn test_get_files_by_group_id_not_found() {
        let a = sample_assay();
        let files = a.get_files_by_group_id("nonexistent", 0);
        assert!(files.is_none());
    }
}