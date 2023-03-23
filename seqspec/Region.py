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
        order: int = 0,
        sequence: str = "",
        min_len: int = 0,
        max_len: int = 1024,
        onlist: Optional["Onlist"] = None,
        regions: Optional[List["Region"]] = None
        # join: Optional["Join"] = None,
    ) -> None:
        super().__init__()
        self.parent_id = None
        self.region_id = region_id
        self.region_type = region_type
        self.name = name
        self.sequence_type = sequence_type
        self.order = order
        self.sequence = sequence

        self.min_len = min_len
        self.max_len = max_len

        self.onlist = onlist
        self.regions = regions
        # self.join = join

        if self.regions:
            self.min_len, self.max_len = self.get_len()

            self.sequence = self.get_sequence()

    def set_parent_id(self, parent_id):
        if self.regions:
            parent_id = self.region_id
            for r in self.regions:
                r.set_parent_id(parent_id)
        else:
            self.parent_id = parent_id
        return

    def get_sequence(self, s: str = "") -> str:
        # take into account "order" property
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

    def update_attr(self, order=0):
        if self.regions:
            for idx, r in enumerate(self.regions):
                r.update_attr(idx)

        self.sequence = self.get_sequence()
        self.min_len, self.max_len = self.get_len()
        self.order = order
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


class Onlist(yaml.YAMLObject):
    yaml_tag = "!Onlist"

    def __init__(self, filename: str, md5: str) -> None:
        super().__init__()
        self.filename = filename
        self.md5 = md5

    def __repr__(self) -> str:
        d = {
            "filename": self.filename,
            "md5": self.md5,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "filename": self.filename,
            "md5": self.md5,
        }
        return d
