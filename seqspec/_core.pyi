from typing import List, Optional, Tuple

class File:
    file_id: str
    filename: str
    filetype: str
    filesize: int
    url: str
    urltype: str
    md5: str

    def __init__(
        self,
        file_id: str,
        filename: str,
        filetype: str,
        filesize: int,
        url: str,
        urltype: str,
        md5: str,
    ) -> None: ...
    @staticmethod
    def from_json(json_str: str) -> "File": ...
    def to_json(self) -> str: ...

class Onlist:
    file_id: str
    filename: str
    filetype: str
    filesize: int
    url: str
    urltype: str
    md5: str

    def __init__(
        self,
        file_id: str,
        filename: str,
        filetype: str,
        filesize: int,
        url: str,
        urltype: str,
        md5: str,
    ) -> None: ...
    @staticmethod
    def from_json(json_str: str) -> "Onlist": ...
    def to_json(self) -> str: ...

class Read:
    read_id: str
    name: str
    modality: str
    primer_id: str
    min_len: int
    max_len: int
    strand: str
    files: list[File]

    def __init__(
        self,
        read_id: str,
        name: str,
        modality: str,
        primer_id: str,
        min_len: int,
        max_len: int,
        strand: str,
        files: list[File] = ...,
    ) -> None: ...
    @staticmethod
    def from_json(json_str: str) -> "Read": ...
    def to_json(self) -> str: ...
    def update_files(self, files: list[File]) -> None: ...
    def update_read_by_id(
        self,
        read_id: str | None,
        name: str | None,
        modality: str | None,
        primer_id: str | None,
        min_len: int | None,
        max_len: int | None,
        strand: str | None,
        files: list[File] | None,
    ) -> None: ...
    def get_read_by_file_id(self, file_id: str) -> "Read | None": ...

# seqspec/_core.pyi (add alongside File/Onlist/Read)

class Region:
    region_id: str
    region_type: str
    name: str
    sequence_type: str
    sequence: str
    min_len: int
    max_len: int
    onlist: Optional[Onlist]
    regions: List["Region"]

    def __init__(
        self,
        region_id: str,
        region_type: str,
        name: str,
        sequence_type: str,
        sequence: str,
        min_len: int,
        max_len: int,
        onlist: Optional[Onlist] = ...,
        regions: List["Region"] = ...,
    ) -> None: ...
    @staticmethod
    def from_json(json_str: str) -> "Region": ...
    def to_json(self) -> str: ...

    # Core helpers
    def get_sequence(self) -> str: ...
    def get_len(self) -> Tuple[int, int]: ...
    def update_attr(self) -> None: ...

    # Queries
    def get_region_by_id(self, region_id: str) -> List["Region"]: ...
    def get_region_by_region_type(self, region_type: str) -> List["Region"]: ...
    def get_onlist_regions(self) -> List["Region"]: ...
    def get_onlist(self) -> Optional[Onlist]: ...
    def get_leaves(self) -> List["Region"]: ...
    def get_leaves_with_region_id(self, region_id: str) -> List["Region"]: ...
    def get_leaf_region_types(self) -> List[str]: ...
    def to_newick(self) -> str: ...

    # Mutations
    def update_region(
        self,
        region_id: str,
        region_type: str,
        name: str,
        sequence_type: str,
        sequence: str,
        min_len: int,
        max_len: int,
        onlist: Optional[Onlist],
    ) -> None: ...
    def update_region_by_id(
        self,
        target_region_id: str,
        region_id: Optional[str] = ...,
        region_type: Optional[str] = ...,
        name: Optional[str] = ...,
        sequence_type: Optional[str] = ...,
        sequence: Optional[str] = ...,
        min_len: Optional[int] = ...,
        max_len: Optional[int] = ...,
    ) -> None: ...

    # Transforms
    def reverse(self) -> None: ...
    def complement(self) -> None: ...
    def __repr__(self) -> str: ...

# ---- Assay metadata records ----------------------------------------
class SeqProtocol:
    protocol_id: str
    name: str
    modality: str
    def __init__(self, protocol_id: str, name: str, modality: str) -> None: ...

class SeqKit:
    kit_id: str
    name: str | None
    modality: str
    def __init__(self, kit_id: str, name: str | None, modality: str) -> None: ...

class LibProtocol:
    protocol_id: str
    name: str
    modality: str
    def __init__(self, protocol_id: str, name: str, modality: str) -> None: ...

class LibKit:
    kit_id: str
    name: str | None
    modality: str
    def __init__(self, kit_id: str, name: str | None, modality: str) -> None: ...

# ---- Assay ----------------------------------------------------------

class Assay:
    seqspec_version: Optional[str]
    assay_id: str
    name: str
    doi: str
    date: str
    description: str
    modalities: List[str]
    lib_struct: str

    # lists of typed objects (or None)
    sequence_protocol: Optional[List[SeqProtocol]]
    sequence_kit: Optional[List[SeqKit]]
    library_protocol: Optional[List[LibProtocol]]
    library_kit: Optional[List[LibKit]]

    # specs
    sequence_spec: List["Read"]
    library_spec: List["Region"]

    def __init__(
        self,
        assay_id: str,
        name: str,
        doi: str,
        date: str,
        description: str,
        modalities: List[str],
        lib_struct: str,
        sequence_spec: List["Read"] = ...,
        library_spec: List["Region"] = ...,
        sequence_protocol: Optional[List[SeqProtocol]] = ...,
        sequence_kit: Optional[List[SeqKit]] = ...,
        library_protocol: Optional[List[LibProtocol]] = ...,
        library_kit: Optional[List[LibKit]] = ...,
        seqspec_version: Optional[str] = ...,
    ) -> None: ...

    # JSON I/O
    @staticmethod
    def from_json(json_str: str) -> "Assay": ...
    def to_json(self) -> str: ...

    # helpers / queries
    def update_spec(self) -> None: ...
    def list_modalities(self) -> List[str]: ...
    def get_libspec(self, modality: str) -> "Region": ...
    def get_seqspec(self, modality: str) -> List["Read"]: ...
    def get_read(self, read_id: str) -> "Read": ...

    # mutations
    def insert_regions(
        self, regions: List["Region"], modality: str, after: str | None = ...
    ) -> None: ...
    def insert_reads(
        self, reads: List["Read"], modality: str, after: str | None = ...
    ) -> None: ...
    def __repr__(self) -> str: ...
