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
        return str(self.model_dump())

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
            if f.filename == file_id:
                return self
        return None


class ReadCoordinate(BaseModel):
    read: Read
    rcv: List[RegionCoordinate]


class ReadInput(LLMInput):
    read_id: Optional[str]
    name: Optional[str]
    modality: Optional[str]
    primer_id: Optional[str]
    min_len: Optional[int]
    max_len: Optional[int]
    strand: Optional[str]
    files: Optional[List[FileInput]] = []

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


# import yaml
# from typing import List, Optional
# from seqspec.File import File
# from seqspec.Region import RegionCoordinate


# class Read(yaml.YAMLObject):
#     yaml_tag = "!Read"

#     def __init__(
#         self,
#         read_id: str,
#         name: str,
#         modality: str,
#         primer_id: str,
#         min_len: int,
#         max_len: int,
#         strand: str,
#         files: List["File"] = [],
#     ) -> None:
#         super().__init__()
#         self.read_id = read_id
#         self.name = name
#         self.modality = modality
#         self.primer_id = primer_id
#         self.min_len = min_len
#         self.max_len = max_len
#         self.strand = strand
#         self.files = files

#     def set_files(self, files: Optional[List["File"]] = []):
#         self.files = files

#     def __repr__(self) -> str:
#         d = self.to_dict()
#         return f"{d}"

#     def to_dict(self):
#         # TODO is this necessary for backwards compatibility?
#         files = getattr(self, "files", [])
#         files = [i.to_dict() for i in files]
#         d = {
#             "read_id": self.read_id,
#             "name": self.name,
#             "modality": self.modality,
#             "primer_id": self.primer_id,
#             "min_len": self.min_len,
#             "max_len": self.max_len,
#             "strand": self.strand,
#             "files": files,
#         }
#         return d

#     def update_read_by_id(
#         self, read_id, name, modality, primer_id, min_len, max_len, strand, files
#     ):
#         if read_id:
#             self.read_id = read_id
#         if name:
#             self.name = name
#         if modality:
#             self.modality = modality
#         if primer_id:
#             self.primer_id = primer_id
#         if min_len:
#             self.min_len = min_len
#         if max_len:
#             self.max_len = max_len
#         if strand:
#             self.strand = strand
#         if files:
#             self.files = files
#         return

#     def get_read_by_file_id(self, file_id):
#         if self.files:
#             for f in self.files:
#                 if f.filename == file_id:
#                     return self
#         return None


# class ReadCoordinate:
#     def __init__(self, read: Read, rcv: List[RegionCoordinate]) -> None:
#         self.read = read
#         self.rcv = rcv
