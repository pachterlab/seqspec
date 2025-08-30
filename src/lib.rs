pub fn sum_as_string(a: usize, b: usize) -> String {
    (a + b).to_string()
}

pub mod file;
pub mod region;
pub mod types;
pub mod assay;
pub mod read;
pub mod onlist;

#[cfg(feature = "python-binding")]
mod py_module;  // lives in src/py_module.rs