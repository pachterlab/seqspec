use serde::Deserialize;
use std::path::Path;

use crate::models::assay::{Assay, LibKit, LibProtocol, SeqKit, SeqProtocol};
use crate::models::file::File;
use crate::models::onlist::Onlist;
use crate::models::read::Read;
use crate::models::region::Region;

#[derive(Clone, Debug, Deserialize)]
pub struct AssayCompat {
    pub seqspec_version: Option<String>,
    pub assay_id: Option<String>,
    pub name: Option<String>,
    pub doi: Option<String>,
    pub date: Option<String>,
    pub description: Option<String>,
    pub modalities: Option<Vec<String>>,
    pub lib_struct: Option<String>,

    pub sequence_protocol: Option<CompatField<CompatSeqProtocol>>,
    pub sequence_kit: Option<CompatField<CompatSeqKit>>,
    pub library_protocol: Option<CompatField<CompatLibProtocol>>,
    pub library_kit: Option<CompatField<CompatLibKit>>,

    pub sequence_spec: Option<Vec<CompatRead>>,
    pub library_spec: Option<Vec<CompatRegion>>,
}

impl AssayCompat {
    pub fn into_assay(self) -> Assay {
        let modalities = self.modalities.unwrap_or_default();
        Assay::new(
            self.assay_id.unwrap_or_default(),
            self.name.unwrap_or_default(),
            self.doi.unwrap_or_default(),
            self.date.unwrap_or_default(),
            self.description.unwrap_or_default(),
            modalities.clone(),
            self.lib_struct.unwrap_or_default(),
            self.sequence_spec
                .unwrap_or_default()
                .into_iter()
                .map(CompatRead::into_read)
                .collect(),
            self.library_spec
                .unwrap_or_default()
                .into_iter()
                .map(CompatRegion::into_region)
                .collect(),
            normalize_field(
                self.sequence_protocol,
                &modalities,
                |value, modality| SeqProtocol {
                    protocol_id: value.clone(),
                    name: value,
                    modality,
                },
                CompatSeqProtocol::into_seqprotocol,
            ),
            normalize_field(
                self.sequence_kit,
                &modalities,
                |value, modality| SeqKit {
                    kit_id: value.clone(),
                    name: Some(value),
                    modality,
                },
                CompatSeqKit::into_seqkit,
            ),
            normalize_field(
                self.library_protocol,
                &modalities,
                |value, modality| LibProtocol {
                    protocol_id: value.clone(),
                    name: value,
                    modality,
                },
                CompatLibProtocol::into_libprotocol,
            ),
            normalize_field(
                self.library_kit,
                &modalities,
                |value, modality| LibKit {
                    kit_id: value.clone(),
                    name: Some(value),
                    modality,
                },
                CompatLibKit::into_libkit,
            ),
            self.seqspec_version,
        )
    }
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
pub enum CompatField<T> {
    Text(String),
    Item(T),
    Items(Vec<CompatFieldItem<T>>),
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
pub enum CompatFieldItem<T> {
    Text(String),
    Item(T),
}

fn normalize_field<Input, Output, FText, FInto>(
    value: Option<CompatField<Input>>,
    modalities: &[String],
    from_text: FText,
    into_output: FInto,
) -> Option<Vec<Output>>
where
    FText: Fn(String, String) -> Output,
    FInto: Fn(Input) -> Output,
{
    let value = value?;
    let mut out = Vec::new();

    match value {
        CompatField::Text(text) => {
            for modality in modalities {
                out.push(from_text(text.clone(), modality.clone()));
            }
        }
        CompatField::Item(item) => out.push(into_output(item)),
        CompatField::Items(items) => {
            for item in items {
                match item {
                    CompatFieldItem::Text(text) => {
                        for modality in modalities {
                            out.push(from_text(text.clone(), modality.clone()));
                        }
                    }
                    CompatFieldItem::Item(item) => out.push(into_output(item)),
                }
            }
        }
    }

    Some(out)
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatSeqProtocol {
    pub protocol_id: Option<String>,
    pub name: Option<String>,
    pub modality: Option<String>,
}

impl CompatSeqProtocol {
    fn into_seqprotocol(self) -> SeqProtocol {
        SeqProtocol {
            protocol_id: self.protocol_id.unwrap_or_else(|| "auto-id".to_string()),
            name: self.name.unwrap_or_default(),
            modality: self.modality.unwrap_or_default(),
        }
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatSeqKit {
    pub kit_id: Option<String>,
    pub name: Option<String>,
    pub modality: Option<String>,
}

impl CompatSeqKit {
    fn into_seqkit(self) -> SeqKit {
        SeqKit {
            kit_id: self.kit_id.unwrap_or_default(),
            name: self.name,
            modality: self.modality.unwrap_or_default(),
        }
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatLibProtocol {
    pub protocol_id: Option<String>,
    pub name: Option<String>,
    pub modality: Option<String>,
}

impl CompatLibProtocol {
    fn into_libprotocol(self) -> LibProtocol {
        LibProtocol {
            protocol_id: self.protocol_id.unwrap_or_default(),
            name: self.name.unwrap_or_default(),
            modality: self.modality.unwrap_or_default(),
        }
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatLibKit {
    pub kit_id: Option<String>,
    pub name: Option<String>,
    pub modality: Option<String>,
}

impl CompatLibKit {
    fn into_libkit(self) -> LibKit {
        LibKit {
            kit_id: self.kit_id.unwrap_or_default(),
            name: self.name,
            modality: self.modality.unwrap_or_default(),
        }
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatFile {
    pub file_id: Option<String>,
    pub filename: Option<String>,
    pub filetype: Option<String>,
    pub filesize: Option<i64>,
    pub url: Option<String>,
    pub urltype: Option<String>,
    pub md5: Option<String>,
}

impl CompatFile {
    fn into_file(self) -> File {
        let filename = self.filename.unwrap_or_default();
        let basename = if filename.is_empty() {
            String::new()
        } else {
            Path::new(&filename)
                .file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .unwrap_or_default()
        };
        let filetype = if let Some(filetype) = self.filetype {
            filetype
        } else if filename.is_empty() {
            String::new()
        } else {
            Path::new(&filename)
                .extension()
                .map(|ext| ext.to_string_lossy().into_owned())
                .unwrap_or_default()
        };

        File::new(
            self.file_id.unwrap_or(basename),
            filename,
            filetype,
            self.filesize.unwrap_or_default(),
            self.url.unwrap_or_default(),
            self.urltype.unwrap_or_else(|| "local".to_string()),
            self.md5.unwrap_or_default(),
        )
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatOnlist {
    pub file_id: Option<String>,
    pub filename: Option<String>,
    pub filetype: Option<String>,
    pub filesize: Option<i64>,
    pub url: Option<String>,
    pub urltype: Option<String>,
    pub md5: Option<String>,
}

impl CompatOnlist {
    fn into_onlist(self) -> Onlist {
        Onlist::new(
            self.file_id.unwrap_or_default(),
            self.filename.unwrap_or_default(),
            self.filetype.unwrap_or_default(),
            self.filesize.unwrap_or_default(),
            self.url.unwrap_or_default(),
            self.urltype.unwrap_or_else(|| "local".to_string()),
            self.md5.unwrap_or_default(),
        )
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatRead {
    pub read_id: Option<String>,
    pub name: Option<String>,
    pub modality: Option<String>,
    pub primer_id: Option<String>,
    pub min_len: Option<i64>,
    pub max_len: Option<i64>,
    pub strand: Option<String>,
    pub files: Option<Vec<CompatFile>>,
}

impl CompatRead {
    fn into_read(self) -> Read {
        let read_id = self.read_id.unwrap_or_default();
        Read::new(
            read_id.clone(),
            self.name.unwrap_or_else(|| read_id.clone()),
            self.modality.unwrap_or_default(),
            self.primer_id.unwrap_or_default(),
            self.min_len.unwrap_or_default(),
            self.max_len.unwrap_or_default(),
            self.strand.unwrap_or_else(|| "pos".to_string()),
            self.files
                .unwrap_or_default()
                .into_iter()
                .map(CompatFile::into_file)
                .collect(),
        )
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct CompatRegion {
    pub region_id: Option<String>,
    pub region_type: Option<String>,
    pub name: Option<String>,
    pub sequence_type: Option<String>,
    pub sequence: Option<String>,
    pub min_len: Option<i64>,
    pub max_len: Option<i64>,
    pub onlist: Option<CompatOnlist>,
    pub regions: Option<Vec<CompatRegion>>,
}

impl CompatRegion {
    fn into_region(self) -> Region {
        let region_id = self.region_id.unwrap_or_default();
        let min_len = self.min_len.unwrap_or_default();
        let max_len = self
            .max_len
            .unwrap_or(if min_len == 0 { 1024 } else { min_len });
        let sequence_type = self.sequence_type.unwrap_or_else(|| "fixed".to_string());
        let sequence = match self.sequence {
            Some(sequence) => sequence,
            None if sequence_type == "random" => "X".repeat(min_len as usize),
            None if sequence_type == "onlist" => "N".repeat(min_len as usize),
            None => String::new(),
        };

        Region::new(
            region_id.clone(),
            self.region_type.unwrap_or_else(|| region_id.clone()),
            self.name.unwrap_or(region_id),
            sequence_type,
            sequence,
            min_len,
            max_len,
            self.onlist.map(CompatOnlist::into_onlist),
            self.regions
                .unwrap_or_default()
                .into_iter()
                .map(CompatRegion::into_region)
                .collect(),
        )
    }
}
