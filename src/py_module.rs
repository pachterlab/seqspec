#[cfg(feature = "python-binding")]
use pyo3::prelude::*;

#[cfg_attr(feature = "python-binding", pyo3::pymodule)]
fn _core(_py: Python<'_>, m: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    m.add_class::<crate::models::file::File>()?;
    m.add_class::<crate::models::read::Read>()?;
    m.add_class::<crate::models::onlist::Onlist>()?;
    m.add_class::<crate::models::region::Region>()?;
    m.add_class::<crate::models::assay::SeqProtocol>()?;
    m.add_class::<crate::models::assay::SeqKit>()?;
    m.add_class::<crate::models::assay::LibProtocol>()?;
    m.add_class::<crate::models::assay::LibKit>()?;
    m.add_class::<crate::models::assay::Assay>()?;
    Ok(())
}