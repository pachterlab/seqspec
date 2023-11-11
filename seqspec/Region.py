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

    def get_onlist(self):
        return self.onlist

    def update_attr(self):
        if self.regions:
            for idx, r in enumerate(self.regions):
                r.update_attr()

        self.sequence = self.get_sequence()
        self.min_len, self.max_len = self.get_len()
        if self.sequence_type == "random" or self.sequence_type == "onlist":
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

    def get_region_by_type(self, region_type, found=[]):
        if not found:
            found = []
        if self.region_type == region_type:
            found.append(self)
        if self.regions:
            for r in self.regions:
                found = r.get_region_by_type(region_type, found)
        return found

    def get_onlist_regions(self, found=[]):
        if not found:
            found = []
        if self.onlist is not None:
            found.append(self)
        if self.regions:
            for r in self.regions:
                found = r.get_onlist_regions(found)
        return found

    def get_leaves(self, leaves=[]):
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


class Onlist(yaml.YAMLObject):
    yaml_tag = "!Onlist"

    def __init__(self, filename: str, md5: str, location: str) -> None:
        super().__init__()
        self.filename = filename
        self.md5 = md5
        self.location = location

    def __repr__(self) -> str:
        d = {
            "filename": self.filename,
            "location": self.location,
            "md5": self.md5,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "filename": self.filename,
            "location": self.location,
            "md5": self.md5,
        }
        return d
