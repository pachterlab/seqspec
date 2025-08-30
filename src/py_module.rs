#[cfg(feature = "python-binding")]
use pyo3::prelude::*;

#[cfg_attr(feature = "python-binding", pyo3::pymodule)]
fn _core(_py: Python<'_>, m: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    m.add_class::<crate::file::File>()?;
    m.add_class::<crate::read::Read>()?;
    m.add_class::<crate::onlist::Onlist>()?;
    m.add_class::<crate::region::Region>()?;
    m.add_class::<crate::assay::SeqProtocol>()?;
    m.add_class::<crate::assay::SeqKit>()?;
    m.add_class::<crate::assay::LibProtocol>()?;
    m.add_class::<crate::assay::LibKit>()?;
    m.add_class::<crate::assay::Assay>()?;
    Ok(())
}