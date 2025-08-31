use crate::models::assay::Assay;

use serde_yaml;


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

// pub fn to_pydict<T: serde::Serialize>(py: Python<'_>, v: &T) -> Result<PyObject, serde_json::Error> {
//     let obj = pythonize::pythonize(py, v)?;
//     Ok(obj.into())
// }


pub fn load_spec(spec: &std::path::PathBuf) -> Assay {
    // read in the spec file
    let f: std::fs::File = std::fs::File::open(spec).expect("Could not open file.");

    // convert it to an assay object
    let spec: Assay = serde_yaml::from_reader(f).expect("Could not read values.");

    return spec;
}