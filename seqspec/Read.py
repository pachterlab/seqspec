from typing import List, Optional

from pydantic import BaseModel, Field

from seqspec.File import File, FileInput
from seqspec.llmtools import LLMInput
from seqspec.Region import RegionCoordinate


class Read(BaseModel):
    read_id: str
    name: str
    modality: str
    primer_id: str
    min_len: int
    max_len: int
    strand: str
    files: List[File] = Field(default_factory=list)

    def set_files(self, files: List[File] = []):
        self.files = files

    def __repr__(self) -> str:
        strand = "+" if self.strand == "pos" else "-"
        s = f"""{strand}({self.min_len}, {self.max_len}){self.read_id}:{self.primer_id}"""
        # return str(self.model_dump())
        return s

    def to_dict(self):
        return self.model_dump()

    def update_read_by_id(
        self,
        read_id=None,
        name=None,
        modality=None,
        primer_id=None,
        min_len=None,
        max_len=None,
        strand=None,
        files=None,
    ):
        if read_id:
            self.read_id = read_id
        if name:
            self.name = name
        if modality:
            self.modality = modality
        if primer_id:
            self.primer_id = primer_id
        if min_len:
            self.min_len = min_len
        if max_len:
            self.max_len = max_len
        if strand:
            self.strand = strand
        if files:
            self.files = files

    def get_read_by_file_id(self, file_id: str):
        for f in self.files:
            if f.file_id == file_id:
                return self
        return None


class ReadCoordinate(BaseModel):
    read: Read
    rcv: List[RegionCoordinate]


class ReadInput(LLMInput):
    read_id: Optional[str] = None
    name: Optional[str] = None
    modality: Optional[str] = None
    primer_id: Optional[str] = None
    min_len: Optional[int] = None
    max_len: Optional[int] = None
    strand: Optional[str] = None
    files: Optional[List[FileInput]] = None

    def to_read(self) -> Read:
        return Read(
            read_id=self.read_id or "",
            name=self.name or self.read_id or "",
            modality=self.modality or "",
            primer_id=self.primer_id or "",
            min_len=self.min_len or 0,
            max_len=self.max_len or 0,
            strand=self.strand or "pos",
            files=[f.to_file() for f in self.files] if self.files else [],
        )
