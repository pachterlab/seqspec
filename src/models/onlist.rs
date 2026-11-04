use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Onlist {
    pub file_id: String,
    pub filename: String,
    pub filetype: String,
    pub filesize: i64,
    pub url: String,
    pub urltype: String,
    pub md5: String,
    #[serde(default)]
    pub sequence_column_index: usize,
    #[serde(default)]
    pub skip_rows: usize,
}

impl Onlist {
    pub fn new(
        file_id: String,
        filename: String,
        filetype: String,
        filesize: i64,
        url: String,
        urltype: String,
        md5: String,
        sequence_column_index: usize,
        skip_rows: usize,
    ) -> Self {
        Self {
            file_id,
            filename,
            filetype,
            filesize,
            url,
            urltype,
            md5,
            sequence_column_index,
            skip_rows,
        }
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

    fn sample_onlist() -> Onlist {
        Onlist::new(
            "ol1".into(),
            "barcodes.txt".into(),
            "txt".into(),
            1024,
            "barcodes.txt".into(),
            "local".into(),
            "abc123".into(),
            0,
            0,
        )
    }

    #[test]
    fn test_onlist_creation() {
        let ol = sample_onlist();
        assert_eq!(ol.file_id, "ol1");
        assert_eq!(ol.filename, "barcodes.txt");
        assert_eq!(ol.filetype, "txt");
        assert_eq!(ol.filesize, 1024);
        assert_eq!(ol.url, "barcodes.txt");
        assert_eq!(ol.urltype, "local");
        assert_eq!(ol.md5, "abc123");
        assert_eq!(ol.sequence_column_index, 0);
        assert_eq!(ol.skip_rows, 0);
    }

    #[test]
    fn test_onlist_json_roundtrip() {
        let mut ol = sample_onlist();
        ol.sequence_column_index = 1;
        ol.skip_rows = 1;
        let json = ol.to_json().unwrap();
        let ol2 = Onlist::from_json(&json).unwrap();
        assert_eq!(ol, ol2);
    }

    #[test]
    fn test_onlist_json_defaults_projection_for_legacy_data() {
        let json = r#"{
            "file_id":"ol1",
            "filename":"barcodes.txt",
            "filetype":"txt",
            "filesize":1024,
            "url":"barcodes.txt",
            "urltype":"local",
            "md5":"abc123"
        }"#;

        let onlist = Onlist::from_json(json).unwrap();

        assert_eq!(onlist.sequence_column_index, 0);
        assert_eq!(onlist.skip_rows, 0);
    }

    #[test]
    fn test_onlist_clone() {
        let ol = sample_onlist();
        let ol2 = ol.clone();
        assert_eq!(ol, ol2);
    }
}
