from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from seqspec.llmtools import LLMInput


class File(BaseModel):
    file_id: str
    filename: str
    filetype: str
    filesize: int
    url: str
    urltype: str
    md5: str

    def __repr__(self) -> str:
        return str(self.model_dump())

    def to_dict(self):
        return self.model_dump()

    def update_file_id(self, file_id: str):
        self.file_id = file_id


class FileInput(LLMInput):
    file_id: Optional[str] = None
    filename: Optional[str] = None
    filetype: Optional[str] = None
    filesize: Optional[int] = None
    url: Optional[str] = None
    urltype: Optional[str] = None
    md5: Optional[str] = None

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
