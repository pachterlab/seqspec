use pyo3::prelude::*;

pub fn complement_base(c: char) -> char {
    match c {
        'A' => 'T', 'T' => 'A', 'G' => 'C', 'C' => 'G',
        'R' => 'Y', 'Y' => 'R', 'S' => 'S', 'W' => 'W',
        'K' => 'M', 'M' => 'K', 'B' => 'V', 'D' => 'H',
        'V' => 'B', 'H' => 'D', 'N' => 'N', 'X' => 'X',
        _ => 'N',
    }
}

pub fn complement_seq(s: &str) -> String {
    s.chars().map(|c| complement_base(c.to_ascii_uppercase())).collect()
}

pub fn to_pydict<T: serde::Serialize>(py: Python<'_>, v: &T) -> PyResult<PyObject> {
    let obj = pythonize::pythonize(py, v)?;
    Ok(obj.into())
}