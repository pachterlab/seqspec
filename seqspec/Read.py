from typing import List, Optional

from pydantic import BaseModel, Field

from seqspec.File import File, FileInput
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
        return s

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


class ReadInput(BaseModel):
    """
    Input payload for constructing a `Read` (sequencing read definition).

    Defaults and behaviors applied in `to_read()`:
    - `read_id`: stable identifier for the read; defaults to empty string.
    - `name`: user label; defaults to `read_id` when omitted.
    - `modality`: modality name this read belongs to (e.g., 'rna', 'atac').
    - `primer_id`: identifier of the primer initiating this read if applicable.
    - `min_len`/`max_len`: expected observed bounds; default to 0.
    - `strand`: 'pos' or 'neg'; defaults to 'pos'.
    - `files`: optional list of `FileInput` defining associated FASTQs or other files.
    """

    read_id: Optional[str] = Field(
        default=None,
        description=(
            "Stable identifier for this read within the assay (e.g., 'R1', 'R2')."
        ),
    )
    name: Optional[str] = Field(
        default=None,
        description=(
            "Human-readable name for the read. Defaults to `read_id` when omitted."
        ),
    )
    modality: Optional[str] = Field(
        default=None,
        description=(
            "Modality this read belongs to (e.g., 'rna', 'atac', 'protein'). Modality must correspond to one of the Assay modalities."
        ),
    )
    primer_id: Optional[str] = Field(
        default=None,
        description=(
            "Identifier for the primer used to generate this read, if relevant."
        ),
    )
    min_len: Optional[int] = Field(
        default=None,
        description=(
            "Minimum expected read length in bases; defaults to 0 if omitted."
        ),
    )
    max_len: Optional[int] = Field(
        default=None,
        description=(
            "Maximum expected read length in bases; defaults to 0 if omitted."
        ),
    )
    strand: Optional[str] = Field(
        default=None,
        description=(
            "Read strand orientation relative to the library structure: 'pos' or 'neg'. Defaults to 'pos'."
        ),
    )
    files: Optional[List[FileInput]] = Field(
        default=None,
        description=(
            "Optional file descriptors (e.g., FASTQs) as File objects with this read."
        ),
    )

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
