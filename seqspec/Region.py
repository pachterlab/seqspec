from enum import Enum
from typing import List, Optional, Set, Union

from pydantic import BaseModel

from seqspec.llmtools import LLMInput


class SequenceType(str, Enum):
    FIXED = "fixed"
    RANDOM = "random"
    ONLIST = "onlist"
    JOINED = "joined"


class RegionType(str, Enum):
    ATAC = "atac"
    BARCODE = "barcode"
    CDNA = "cdna"
    CRISPR = "crispr"
    CUSTOM_PRIMER = "custom_primer"
    DNA = "dna"
    FASTQ = "fastq"
    FASTQ_LINK = "fastq_link"
    GDNA = "gdna"
    HIC = "hic"
    ILLUMINA_P5 = "illumina_p5"
    ILLUMINA_P7 = "illumina_p7"
    INDEX5 = "index5"
    INDEX7 = "index7"
    LINKER = "linker"
    ME1 = "ME1"
    ME2 = "ME2"
    METHYL = "methyl"
    NAMED = "named"
    NEXTERA_READ1 = "nextera_read1"
    NEXTERA_READ2 = "nextera_read2"
    POLY_A = "poly_A"
    POLY_G = "poly_G"
    POLY_T = "poly_T"
    POLY_C = "poly_C"
    PROTEIN = "protein"
    RNA = "rna"
    S5 = "s5"
    S7 = "s7"
    TAG = "tag"
    TRUSEQ_READ1 = "truseq_read1"
    TRUSEQ_READ2 = "truseq_read2"
    UMI = "umi"
    DIFFERENCE = "difference"


class Onlist(BaseModel):
    file_id: str
    filename: str
    filetype: str
    filesize: int
    url: str
    urltype: str
    md5: str


class OnlistInput(LLMInput):
    file_id: Optional[str]
    filename: Optional[str]
    filetype: Optional[str]
    filesize: Optional[int]
    url: Optional[str]
    urltype: Optional[str]
    md5: Optional[str]

    def to_onlist(self) -> Onlist:
        return Onlist(
            file_id=self.file_id or "",
            filename=self.filename or "",
            filetype=self.filetype or "",
            filesize=self.filesize or 0,
            url=self.url or "",
            urltype=self.urltype or "local",
            md5=self.md5 or "",
        )


class Region(BaseModel):
    region_id: str
    region_type: Union[str, RegionType]
    name: str
    sequence_type: Union[str, SequenceType]
    sequence: str = ""
    min_len: int = 0
    max_len: int = 1024
    onlist: Optional[Onlist] = None
    regions: Optional[List["Region"]] = None
    # parent_id: Optional[str] = None

    # def set_parent_id(self, parent_id: str):
    #     self.parent_id = parent_id
    #     if self.regions:
    #         for r in self.regions:
    #             r.set_parent_id(self.region_id)

    def get_sequence(self, s: str = "") -> str:
        if self.regions:
            for r in self.regions:
                s = r.get_sequence(s)
        else:
            s += self.sequence if self.sequence is not None else "X"
        return s

    def get_len(self, min_l: int = 0, max_l: int = 0):
        if self.regions:
            for r in self.regions:
                min_l, max_l = r.get_len(min_l, max_l)
        else:
            min_l += self.min_len
            max_l += self.max_len
        return (min_l, max_l)

    def update_attr(self):
        if self.regions:
            for r in self.regions:
                r.update_attr()
        self.sequence = self.get_sequence()
        self.min_len, self.max_len = self.get_len()
        if self.sequence_type == "random":
            self.sequence = "X" * self.min_len
        elif self.sequence_type == "onlist":
            self.sequence = "N" * self.min_len

    def get_region_by_id(
        self, region_id: str, found: Optional[List["Region"]] = None
    ) -> List["Region"]:
        if found is None:
            found = []
        if self.region_id == region_id:
            found.append(self)
        if self.regions:
            for r in self.regions:
                r.get_region_by_id(region_id, found)
        return found

    def get_region_by_region_type(
        self, region_type: str, found: Optional[List["Region"]] = None
    ) -> List["Region"]:
        if found is None:
            found = []
        if str(self.region_type) == str(region_type):
            found.append(self)
        if self.regions:
            for r in self.regions:
                r.get_region_by_region_type(region_type, found)
        return found

    def get_onlist_regions(
        self, found: Optional[List["Region"]] = None
    ) -> List["Region"]:
        if found is None:
            found = []
        if self.onlist:
            found.append(self)
        if self.regions:
            for r in self.regions:
                r.get_onlist_regions(found)
        return found

    def get_onlist(self) -> Optional[Onlist]:
        """Get the onlist associated with this region."""
        return self.onlist

    def get_leaves(self, leaves: Optional[List["Region"]] = None) -> List["Region"]:
        # print(leaves)
        if leaves is None:
            leaves = []
        if not self.regions:
            leaves.append(self)
            # print(leaves)
        else:
            for r in self.regions:
                r.get_leaves(leaves)
        return leaves

    def get_leaf_region_types(self) -> Set[str]:
        return set(r.region_type for r in self.get_leaves())

    def to_newick(self, n="") -> str:
        if self.regions:
            t = [r.to_newick(n) for r in self.regions]
            return f"({','.join(t)}){self.region_id}"
        return f"'{self.region_id}:{self.max_len}'"

    def update_region(
        self,
        region_id,
        region_type,
        name,
        sequence_type,
        sequence,
        min_len,
        max_len,
        onlist,
    ):
        self.region_id = region_id
        self.region_type = region_type
        self.name = name
        self.sequence_type = sequence_type
        self.sequence = sequence
        self.min_len = min_len
        self.max_len = max_len
        self.onlist = onlist

    def update_region_by_id(
        self,
        target_region_id,
        region_id,
        region_type,
        name,
        sequence_type,
        sequence,
        min_len,
        max_len,
    ):
        target = self.get_region_by_id(target_region_id)
        if target:
            r = target[0]
            r.region_id = region_id or r.region_id
            r.region_type = region_type or r.region_type
            r.name = name or r.name
            r.sequence_type = sequence_type or r.sequence_type
            r.sequence = sequence or r.sequence
            r.min_len = min_len or r.min_len
            r.max_len = max_len or r.max_len

    def reverse(self):
        if self.regions:
            for r in reversed(self.regions):
                r.reverse()
        else:
            self.sequence = self.sequence[::-1]

    def complement(self):
        if self.regions:
            for r in self.regions:
                r.complement()
        else:
            self.sequence = complement_sequence(self.sequence)


Region.model_rebuild()


class RegionInput(LLMInput):
    region_id: Optional[str]
    region_type: Optional[Union[str, RegionType]]
    name: Optional[str]
    sequence_type: Optional[Union[str, SequenceType]]
    sequence: Optional[str]
    min_len: Optional[int]
    max_len: Optional[int]
    onlist: Optional[OnlistInput]
    # regions: Optional[List["RegionInput"]] = None
    # parent_id: Optional[str]

    def to_region(self) -> Region:
        length = self.min_len or self.max_len or 0
        seq_type = self.sequence_type or "fixed"
        sequence = "X" * length if seq_type == "random" else self.sequence or ""
        return Region(
            region_id=self.region_id or "",
            region_type=self.region_type or self.region_id or "",
            name=self.name or self.region_id or "",
            sequence_type=seq_type,
            sequence=sequence,
            min_len=length,
            max_len=length,
            onlist=self.onlist.to_onlist() if self.onlist else None,
            regions=None,  # [r.to_region() for r in self.regions] if self.regions else None,
            # parent_id=self.parent_id,
        )


RegionInput.model_rebuild()


class RegionCoordinate(Region):
    start: int = 0
    stop: int = 0

    def __str__(self):
        return f"RegionCoordinate {self.name} [{self.region_type}]: [{self.start}, {self.stop})"

    def __sub__(self, other):
        if not isinstance(other, RegionCoordinate):
            raise TypeError(
                "Subtraction only supported between RegionCoordinate objects"
            )

        if self.stop <= other.start:
            new_start, new_stop = self.stop, other.start
        elif other.stop <= self.start:
            new_start, new_stop = other.stop, self.start
        elif self.start == other.start and self.stop == other.stop:
            new_start, new_stop = self.start, self.stop
        else:
            raise ValueError("Subtraction is not defined.")

        new_region = RegionCoordinate(
            region_id=f"{self.region_id} - {other.region_id}",
            region_type="difference",
            name=f"{self.name} - {other.name}",
            sequence_type="diff",
            sequence="X",
            min_len=abs(new_stop - new_start),
            max_len=abs(new_stop - new_start),
            start=new_start,
            stop=new_stop,
        )
        new_region.sequence = "X" * new_region.min_len
        return new_region


class RegionCoordinateDifference(BaseModel):
    obj: RegionCoordinate
    fixed: RegionCoordinate
    rgncdiff: RegionCoordinate
    loc: Optional[str] = ""

    def __init__(self, **data):
        super().__init__(**data)
        if self.obj.stop <= self.fixed.start:
            self.loc = "-"
        elif self.obj.start >= self.fixed.stop:
            self.loc = "+"


def project_regions_to_coordinates(
    regions: List[Region], rcs: Optional[List[RegionCoordinate]] = None
) -> List[RegionCoordinate]:
    rcs = rcs or []
    prev = 0
    for r in regions:
        nxt = prev + r.max_len
        rc = RegionCoordinate(**r.model_dump(), start=prev, stop=nxt)
        rcs.append(rc)
        prev = nxt
    return rcs


def itx_read(
    region_coordinates: List[RegionCoordinate], read_start: int, read_stop: int
) -> List[RegionCoordinate]:
    new_rcs = []
    for rc in region_coordinates:
        if read_start >= rc.stop or read_stop <= rc.start:
            continue
        # Create a new RegionCoordinate instance using model_copy
        rc_copy = rc.model_copy(deep=True)
        if read_start >= rc_copy.start:
            rc_copy.start = read_start
        if read_stop < rc_copy.stop:
            rc_copy.stop = read_stop
        new_rcs.append(rc_copy)

    return new_rcs


def complement_nucleotide(nucleotide: str) -> str:
    complements = {
        "A": "T",
        "T": "A",
        "G": "C",
        "C": "G",
        "R": "Y",
        "Y": "R",
        "S": "S",
        "W": "W",
        "K": "M",
        "M": "K",
        "B": "V",
        "D": "H",
        "V": "B",
        "H": "D",
        "N": "N",
        "X": "X",
    }
    return complements.get(nucleotide, "N")


def complement_sequence(sequence: str) -> str:
    return "".join(complement_nucleotide(n) for n in sequence.upper())
