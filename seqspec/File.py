from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ._core import File as _RustFile

__all__ = ["File"]


class File(BaseModel):
    file_id: str
    filename: str
    filetype: str
    filesize: int
    url: str
    urltype: str
    md5: str

    # add an updatae_spec attr that computes the md5 for the object

    def __repr__(self) -> str:
        return self.file_id


class FileInput(BaseModel):
    """
    Input payload for constructing a `File`.

    How defaults are derived in `to_file()` when fields are omitted:
    - `file_id`: defaults to `Path(filename).name` if `filename` is provided.
    - `filetype`: defaults to the extension of `filename` (without the leading dot).
    - `urltype`: defaults to "local".
    - `filesize`, `md5`, `url`, `filename`: default to empty/zero values if unknown.
    """

    file_id: Optional[str] = Field(
        default=None,
        description=(
            "Stable identifier for the file (human- or system-defined). "
            "If omitted, it is derived from `filename`'s basename."
        ),
    )
    filename: Optional[str] = Field(
        default=None,
        description=(
            "File name or relative path, e.g., 'rna_R1.fastq.gz'. Used to derive "
            "`file_id` and `filetype` when those are not provided."
        ),
    )
    filetype: Optional[str] = Field(
        default=None,
        description=(
            "File format/extension without dot, e.g., 'fastq.gz', 'txt', 'bam'. "
            "Defaults from the extension of `filename`."
        ),
    )
    filesize: Optional[int] = Field(
        default=None,
        description=(
            "File size in bytes if known. Use 0 or omit if not known at creation time."
        ),
    )
    url: Optional[str] = Field(
        default=None,
        description=(
            "Location of the file. Can be a local path or remote URI (e.g., s3://, gs://, http://)."
        ),
    )
    urltype: Optional[str] = Field(
        default=None,
        description=(
            "How to interpret `url` (e.g., 'local', 's3', 'gs', 'http'). Defaults to 'local'."
        ),
    )
    md5: Optional[str] = Field(
        default=None,
        description=(
            "MD5 checksum as a lowercase hex string if available; omit if unknown."
        ),
    )

    def to_file(self) -> File:
        # derive defaults from filename when needed
        fname = self.filename or ""
        return File(
            file_id=self.file_id or (Path(fname).name if fname else ""),
            filename=fname,
            filetype=self.filetype or (Path(fname).suffix.lstrip(".") if fname else ""),
            filesize=self.filesize or 0,
            url=self.url or "",
            urltype=self.urltype or "local",
            md5=self.md5 or "",
        )


class RustFile:
    __slots__ = ("_inner",)

    def __init__(self, inner: _RustFile) -> None:
        self._inner = inner

    @classmethod
    def new(
        cls,
        *,
        file_id: str,
        filename: str,
        filetype: str,
        filesize: int,
        url: str,
        urltype: str,
        md5: str,
    ) -> "RustFile":
        return cls(
            _RustFile(file_id, filename, filetype, int(filesize), url, urltype, md5)
        )

    def __getattr__(self, name):
        # called only if attribute not found on Rust object itself
        return getattr(self._inner, name)

    def __setattr__(self, name, value):
        if name == "_inner":
            object.__setattr__(self, name, value)
        else:
            setattr(self._inner, name, value)

    @classmethod
    def from_model(cls, m: File) -> "RustFile":
        return cls(_RustFile.from_json(m.model_dump_json()))

    @classmethod
    def from_input(cls, i: FileInput) -> "RustFile":
        return cls.from_model(i.to_file())

    def snapshot(self) -> File:
        return File.model_validate_json(self._inner.to_json())

    def __repr__(self) -> str:
        return f"RustFile(file_id={self.file_id!r}, filename={self.filename!r}, size={self.filesize})"
