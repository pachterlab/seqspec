mod compat;

pub mod models;

pub use models::{assay, coordinate, file, onlist, read, region};
pub mod auth;
pub mod seqspec_auth;
pub mod seqspec_check;
pub mod seqspec_file;
pub mod seqspec_find;
pub mod seqspec_format;
pub mod seqspec_html;
pub mod seqspec_index;
pub mod seqspec_info;
pub mod seqspec_init;
pub mod seqspec_insert;
pub mod seqspec_methods;
pub mod seqspec_modify;
pub mod seqspec_onlist;
pub mod seqspec_print;
pub mod seqspec_split;
pub mod seqspec_upgrade;
pub mod seqspec_version;
pub mod utils;

// #[cfg(feature = "python-binding")]
// mod py_module;  // lives in src/py_module.rs
