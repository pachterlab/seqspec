import yaml
from typing import List, Optional
from seqspec.File import File
from seqspec.Region import RegionCoordinate


class Read(yaml.YAMLObject):
    yaml_tag = "!Read"

    def __init__(
        self,
        read_id: str,
        name: str,
        modality: str,
        primer_id: str,
        min_len: int,
        max_len: int,
        strand: str,
        files: List["File"] = [],
    ) -> None:
        super().__init__()
        self.read_id = read_id
        self.name = name
        self.modality = modality
        self.primer_id = primer_id
        self.min_len = min_len
        self.max_len = max_len
        self.strand = strand
        self.files = files

    def set_files(self, files: Optional[List["File"]] = []):
        self.files = files

    def __repr__(self) -> str:
        d = {
            "read_id": self.read_id,
            "name": self.name,
            "modality": self.modality,
            "primer_id": self.primer_id,
            "min_len": self.min_len,
            "max_len": self.max_len,
            "strand": self.strand,
            "files": self.files,
        }
        return f"{d}"

    def to_dict(self):
        # TODO is this necessary for backwards compatibility?
        if self.files:
            files = [i.to_dict() for i in self.files]
        else:
            files = []
        d = {
            "read_id": self.read_id,
            "name": self.name,
            "modality": self.modality,
            "primer_id": self.primer_id,
            "min_len": self.min_len,
            "max_len": self.max_len,
            "strand": self.strand,
            "files": files,
        }
        return d

    def update_read_by_id(
        self, read_id, name, modality, primer_id, min_len, max_len, strand, files
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
        return

    def get_read_by_file_id(self, file_id):
        if self.files:
            for f in self.files:
                if f.filename == file_id:
                    return self
        return None

    def get_filenames(self):
        """Returns the filenames attached to this Read object
        """
        return [getattr(f, "filename", None) for f in getattr(self, "files", [])]


class ReadCoordinate:
    def __init__(self, read: Read, rcv: List[RegionCoordinate]) -> None:
        self.read = read
        self.rcv = rcv
