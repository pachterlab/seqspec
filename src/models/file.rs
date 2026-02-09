use serde::{Deserialize, Serialize};


#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct File {
   pub file_id: String,
   pub filename: String,
   pub filetype: String,
   pub filesize: i64,
   pub url: String,
   pub urltype: String,
   pub md5: String,
}

impl File {
    pub fn new(
        file_id: String, 
        filename: String, 
        filetype: String, 
        filesize: i64,
        url: String, 
        urltype: String, 
        md5: String) -> Self {
        Self { file_id, filename, filetype, filesize, url, urltype, md5 }
    }

    pub fn from_json(json_str: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json_str)
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_file() -> File {
        File::new(
            "file1".into(),
            "reads_R1.fastq.gz".into(),
            "fastq".into(),
            1024,
            "reads_R1.fastq.gz".into(),
            "local".into(),
            "abc123".into(),
        )
    }

    #[test]
    fn test_file_creation() {
        let f = sample_file();
        assert_eq!(f.file_id, "file1");
        assert_eq!(f.filename, "reads_R1.fastq.gz");
        assert_eq!(f.filetype, "fastq");
        assert_eq!(f.filesize, 1024);
        assert_eq!(f.url, "reads_R1.fastq.gz");
        assert_eq!(f.urltype, "local");
        assert_eq!(f.md5, "abc123");
    }

    #[test]
    fn test_file_json_roundtrip() {
        let f = sample_file();
        let json = f.to_json().unwrap();
        let f2 = File::from_json(&json).unwrap();
        assert_eq!(f, f2);
    }

    #[test]
    fn test_file_partial_eq() {
        let f1 = sample_file();
        let f2 = sample_file();
        assert_eq!(f1, f2);

        let f3 = File::new(
            "file2".into(), "other.fq".into(), "fastq".into(),
            0, "".into(), "local".into(), "".into(),
        );
        assert_ne!(f1, f3);
    }

    #[test]
    fn test_file_clone() {
        let f1 = sample_file();
        let f2 = f1.clone();
        assert_eq!(f1, f2);
    }
}