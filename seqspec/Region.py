from typing import Optional, List
import yaml


# todo figure out how to do enums type options
class Region(yaml.YAMLObject):
    yaml_tag = "!Region"

    def __init__(
        self,
        region_id: str,
        region_type: str,
        name: str,
        sequence_type: str,
        sequence: str = "",
        min_len: int = 0,
        max_len: int = 1024,
        onlist: Optional["Onlist"] = None,
        regions: Optional[List["Region"]] = None,
    ) -> None:
        super().__init__()
        self.parent_id = None
        self.region_id = region_id
        self.region_type = region_type
        self.name = name
        self.sequence_type = sequence_type
        self.sequence = sequence

        self.min_len = min_len
        self.max_len = max_len

        self.onlist = onlist
        self.regions = regions

        if self.regions:
            self.min_len, self.max_len = self.get_len()

            self.sequence = self.get_sequence()

    def set_parent_id(self, parent_id):
        self.parent_id = parent_id
        if self.regions:
            parent_id = self.region_id
            for r in self.regions:
                r.set_parent_id(parent_id)

    def get_sequence(self, s: str = "") -> str:
        if self.regions:
            for r in self.regions:
                s = r.get_sequence(s)
        else:
            if self.sequence:
                s += self.sequence
            elif self.sequence is None:
                s += "X"
        return s

    def get_len(self, min_l: int = 0, max_l: int = 0):
        if self.regions:
            for r in self.regions:
                min_l, max_l = r.get_len(min_l, max_l)
        else:
            min_l += self.min_len
            max_l += self.max_len
        return (min_l, max_l)

    def get_onlist(self) -> Optional["Onlist"]:
        return self.onlist

    def update_attr(self):
        if self.regions:
            for idx, r in enumerate(self.regions):
                r.update_attr()

        self.sequence = self.get_sequence()
        self.min_len, self.max_len = self.get_len()
        if self.sequence_type == "random":
            self.sequence = "X" * self.min_len
        if self.sequence_type == "onlist":
            self.sequence = "N" * self.min_len
        return

    def __repr__(self) -> str:
        d = {
            "region_id": self.region_id,
            "region_type": self.region_type,
            "name": self.name,
            "sequence_type": self.sequence_type,
            "onlist": self.onlist,
            "sequence": self.sequence,
            "min_len": self.min_len,
            "max_len": self.max_len,
            "regions": self.regions,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "region_id": self.region_id,
            "region_type": self.region_type,
            "name": self.name,
            "sequence_type": self.sequence_type,
            "onlist": self.onlist.to_dict() if self.onlist else None,
            "sequence": self.sequence,
            "min_len": self.min_len,
            "max_len": self.max_len,
            "regions": [i.to_dict() for i in (self.regions or [])],
        }
        return d

    def to_newick(self, n=""):
        if self.regions:
            t = []
            for r in self.regions:
                t.append(f"{r.to_newick(n)}")
                n = f"({','.join(t)}){r.parent_id}"
        else:
            n = f"'{self.region_id}:{self.max_len}'"

        return n

    def get_region_by_id(self, region_id, found=[]):
        if not found:
            found = []
        if self.region_id == region_id:
            found.append(self)
        if self.regions:
            for r in self.regions:
                found = r.get_region_by_id(region_id, found)
        return found

    def get_region_by_region_type(
        self, region_type: str, found: List["Region"] = []
    ) -> List["Region"]:
        if not found:
            found = []
        if self.region_type == region_type:
            found.append(self)
        if self.regions:
            for r in self.regions:
                found = r.get_region_by_region_type(region_type, found)
        return found

    def get_onlist_regions(self, found: List["Region"] = []) -> List["Region"]:
        if not found:
            found = []
        if self.onlist is not None:
            found.append(self)
        if self.regions:
            for r in self.regions:
                found = r.get_onlist_regions(found)
        return found

    def get_leaves(self, leaves: List["Region"] = []) -> List["Region"]:
        if not leaves:
            leaves = []
        if not self.regions:
            leaves.append(self)
        else:
            for r in self.regions:
                leaves = r.get_leaves(leaves=leaves)
        return leaves

    def get_leaf_region_types(self):
        leaves = self.get_leaves()
        rtypes = set()
        for r in leaves:
            rtypes.add(r.region_type)
        return rtypes

    # how do I make sure this updates the spec in place?

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
        return

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
        # Identify the target subregion
        target_region = self.get_region_by_id(target_region_id)
        if target_region:
            target_region = target_region[0]  # Assuming region_id is unique
            # Update the properties of the target subregion
            # check if not none
            if region_id:
                target_region.region_id = region_id
            if region_type:
                target_region.region_type = region_type
            if name:
                target_region.name = name
            if sequence_type:
                target_region.sequence_type = sequence_type
            if sequence:
                target_region.sequence = sequence
            if min_len:
                target_region.min_len = min_len
            if max_len:
                target_region.max_len = max_len
        return

    def reverse(self):
        if self.regions:
            # reverse the list of sub regions
            for r in self.regions[::-1]:
                r.reverse()
        else:
            # reverse the actual sequence
            self.sequence = self.sequence[::-1]
        return

    def complement(self):
        if self.regions:
            for r in self.regions:
                r.complement()
        else:
            self.sequence = complement_sequence(self.sequence)


class RegionCoordinate(Region):
    def __init__(
        self,
        region: Region,
        start: int = 0,
        stop: int = 0,
    ):
        super().__init__(
            region.region_id,
            region.region_type,
            region.name,
            region.sequence_type,
            region.sequence,
            region.min_len,
            region.max_len,
            region.onlist,
            region.regions,
        )
        self.start = start
        self.stop = stop

    def __repr__(self) -> str:
        d = {
            "region": self.region_id,
            "start": self.start,
            "stop": self.stop,
        }
        return f"{d}"

    # def __repr__(self):
    #     return f"RegionCoordinate {self.name} [{self.region_type}]: [{self.start}, {self.stop})"

    def __str__(self):
        return f"RegionCoordinate {self.name} [{self.region_type}]: [{self.start}, {self.stop})"

    def __eq__(self, other):
        return self.start == other.start and self.stop == other.stop

    def __sub__(self, other):
        """
        Define the subtraction between two RegionCoordinate objects.
        rc2 - rc1 should return a new RegionCoordinate with:
        - start as rc2.start - rc1.stop
        - stop as rc2.stop - rc1.start
        - min_len and max_len is max(self.start, other.start) - min(self.stop, other.stop)
        """
        if not isinstance(other, RegionCoordinate):
            raise TypeError(
                f"Unsupported operand type(s) for -: 'RegionCoordinate' and '{type(other).__name__}'"
            )

        # Case 1: self is to the left of other
        # need to handle the case where the diff is zero but the position of other is left or right of self
        # self - other
        if self.stop <= other.start:
            new_start = self.stop
            new_stop = other.start

        # Case 2: self is to the right of other
        elif other.stop <= self.start:
            new_start = other.stop
            new_stop = self.start
        else:
            # not so obious what to do with the start and the stop for the same element
            if self.start == other.start and self.stop == other.stop:
                new_start = self.start
                new_stop = self.stop
            else:
                raise ValueError("Subtraction is not defined.")

        # Create a new RegionCoordinate object with the updated start and stop values
        new_region = RegionCoordinate(
            region=Region(
                region_id=f"{self.region_id} - {other.region_id}",
                region_type="difference",
                name=f"{self.name} - {other.name}",
                sequence_type="diff",
                sequence="X",
                min_len=0,
                max_len=0,
                onlist=None,
                regions=None,
            ),  # Assuming the region meta-data stays the same
            start=new_start,
            stop=new_stop,
        )

        # Set min_len and max_len
        new_region.min_len = abs(new_region.stop - new_region.start)
        new_region.max_len = abs(new_region.stop - new_region.start)
        new_region.sequence = "X" * new_region.min_len

        return new_region


class RegionCoordinateDifference:
    def __init__(
        self,
        obj: RegionCoordinate,
        fixed: RegionCoordinate,
        rgncdiff: RegionCoordinate,
        loc: str = "",
    ):
        self.obj = obj
        self.fixed = fixed
        self.rgncdiff = rgncdiff
        self.loc = loc
        if obj.stop <= fixed.start:
            self.loc = "-"
        elif obj.start >= fixed.stop:
            self.loc = "+"

    def __repr__(self) -> str:
        d = {
            "obj": self.obj,
            "fixed": self.fixed,
            "rgncdiff": self.rgncdiff,
            "loc": self.loc,
        }
        return f"{d}"


def project_regions_to_coordinates(
    regions: List[Region], rcs: List[RegionCoordinate] = []
) -> List[RegionCoordinate]:
    if not rcs:
        rcs = []
    prev = 0
    for r in regions:
        nxt = prev + r.max_len
        rc = RegionCoordinate(r, prev, nxt)
        rcs.append(rc)
        prev = nxt
    return rcs


def itx_read(
    region_coordinates: List[RegionCoordinate], read_start: int, read_stop: int
) -> List[RegionCoordinate]:
    # return a list of region_coordinates intersect with read start/stop
    new_rcs = []

    for idx, rc in enumerate(region_coordinates):
        # read start after rc ends, ignore
        if read_start >= rc.stop:
            continue
        # read stop before rc starts, ignore
        if read_stop <= rc.start:
            continue

        # all region_coordinates now have read start or stop in the rc

        # read start in rc, update start
        if read_start >= rc.start:
            rc.start = read_start
        # read stop in rc, update stop
        if read_stop < rc.stop:
            rc.stop = read_stop
        new_rcs.append(rc)

    return new_rcs


class Onlist(yaml.YAMLObject):
    yaml_tag = "!Onlist"

    def __init__(
        self,
        file_id: str,
        filename: str,
        filetype: str,
        filesize: int,
        url: str,
        urltype: str,
        md5: str,
        location: Optional[str],
    ) -> None:
        super().__init__()
        self.file_id = file_id
        self.filename = filename
        self.filetype = filetype
        self.filesize = filesize
        self.url = url
        self.urltype = urltype
        self.md5 = md5
        # to depracate
        # self.location = location

    def __repr__(self) -> str:
        d = {
            "file_id": self.file_id,
            "filename": self.filename,
            "filetype": self.filetype,
            "filesize": self.filesize,
            "url": self.url,
            "urltype": self.urltype,
            "md5": self.md5,
            # "location": self.location,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "file_id": self.file_id,
            "filename": self.filename,
            "filetype": self.filetype,
            "filesize": self.filesize,
            "url": self.url,
            "urltype": self.urltype,
            "md5": self.md5,
            # "location": self.location,
        }
        return d

    def update_file_id(self, file_id):
        self.file_id = file_id


def complement_nucleotide(nucleotide):
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
    return complements.get(
        nucleotide, "N"
    )  # Default to 'N' if nucleotide is not recognized


def complement_sequence(sequence):
    return "".join(complement_nucleotide(n) for n in sequence.upper())
