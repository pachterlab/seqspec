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
        join: Optional["Join"] = None,
    ) -> None:
        super().__init__()
        self.region_id = region_id
        self.region_type = region_type
        self.name = name
        self.sequence_type = sequence_type
        self.sequence = sequence

        self.min_len = min_len
        self.max_len = max_len

        self.onlist = onlist
        self.join = join

        if self.join:
            self.min_len, self.max_len = self.get_len()

            self.sequence = self.get_sequence()

    def get_sequence(self, s: str = "") -> str:
        # take into account "order" property
        if self.join:
            for r in self.join.regions:
                s = r.get_sequence(s)
        else:
            if self.sequence:
                s += self.sequence
            elif self.sequence is None:
                s += "X"
        return s

    def get_len(self, min_l: int = 0, max_l: int = 0):
        if self.join:
            for r in self.join.regions:
                min_l, max_l = r.get_len(min_l, max_l)
        else:
            min_l += self.min_len
            max_l += self.max_len
        return (min_l, max_l)

    def update_attr(self):
        if self.join:
            for r in self.join.regions:
                r.update_attr()

        self.sequence = self.get_sequence()
        self.min_len, self.max_len = self.get_len()
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
            "join": self.join,
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
            "join": self.join.to_dict() if self.join else None,
        }
        return d

    def get_region(self, region_id, found=[]):
        if not found:
            found = []
        if self.region_id == region_id:
            found.append(self)
        if self.join:
            for r in self.join.regions:
                found = r.get_region(region_id, found)
        return found

    def get_leaves(self, leaves=[]):
        if not leaves:
            leaves = []
        if not self.join:
            leaves.append(self)
        else:
            for r in self.join.regions:
                leaves = r.get_leaves(leaves=leaves)
        return leaves


class Join(yaml.YAMLObject):
    yaml_tag = "!Join"

    def __init__(
        self,
        how: str,
        order: List[str],
        regions: List[Region],
    ) -> None:
        super().__init__()
        self.regions = regions
        self.how = how
        self.order = order

    def __repr__(self) -> str:
        d = {
            "how": self.how,
            "order": self.order,
            "regions": self.regions,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "how": self.how,
            "order": self.order,
            "regions": [o.to_dict() for o in self.regions],
        }
        return d


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
