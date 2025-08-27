from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class File(BaseModel):
    file_id: str
    filename: str
    filetype: str
    filesize: int
    url: str
    urltype: str
    md5: str

    def __repr__(self) -> str:
        s = f"""{self.file_id}"""
        return s

    def update_file_id(self, file_id: str):
        self.file_id = file_id


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
        return File(
            file_id=self.file_id or (Path(self.filename).name if self.filename else ""),
            filename=self.filename or "",
            filetype=self.filetype
            or (Path(self.filename).suffix.lstrip(".") if self.filename else ""),
            filesize=self.filesize or 0,
            url=self.url or "",
            urltype=self.urltype or "local",
            md5=self.md5 or "",
        )
