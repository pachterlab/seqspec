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
    ) -> Self {
        Self {
            file_id,
            filename,
            filetype,
            filesize,
            url,
            urltype,
            md5,
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
    }

    #[test]
    fn test_onlist_json_roundtrip() {
        let ol = sample_onlist();
        let json = ol.to_json().unwrap();
        let ol2 = Onlist::from_json(&json).unwrap();
        assert_eq!(ol, ol2);
    }

    #[test]
    fn test_onlist_clone() {
        let ol = sample_onlist();
        let ol2 = ol.clone();
        assert_eq!(ol, ol2);
    }
}
