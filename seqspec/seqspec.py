from typing import Optional, List, Dict
import yaml
import json


# todo figure out how to do enums type options
class Region(yaml.YAMLObject):
    yaml_tag = u'!Region'

    def __init__(self,
                 name: str,
                 sequence_type: str,
                 sequence: str = "",
                 min_len: int = 1,
                 max_len: int = 99,
                 onlist: Optional[str] = None,
                 join: Optional['Join'] = None) -> None:
        self.name = name
        self.sequence_type = sequence_type
        self.sequence = sequence

        self.min_len = min_len
        self.max_len = max_len

        self.onlist = onlist
        self.join = join

        if self.join:
            self.min_len, self.max_len = self.get_len()
            self.max_len += 1

            self.sequence = self.get_sequence()

    def get_sequence(self, s: str = "") -> str:
        if self.join:
            for n, r in self.join.regions.items():
                s = r.get_sequence(s)
        else:
            if self.sequence:
                s += self.sequence
            elif self.sequence is None:
                s += "X"
        return s

    def get_len(self, min_l: int = 0, max_l: int = 0):
        if self.join:
            for n, r in self.join.regions.items():
                min_l, max_l = r.get_len(min_l, max_l)
        else:
            min_l += self.min_len
            max_l += self.max_len - 1
        return (min_l, max_l)

    def update_attr(self):
        if self.join:
            for n, r in self.join.regions.items():
                r.update_attr()

        self.sequence = self.get_sequence()
        self.min_len, self.max_len = self.get_len()
        return

    def __repr__(self) -> str:
        d = {
            "sequence_type": self.sequence_type,
            "onlist": self.onlist,
            "sequence": self.sequence,
            "min_len": self.min_len,
            "max_len": self.max_len,
            "join": self.join
        }
        return f"{d}"


class Join(yaml.YAMLObject):
    yaml_tag = u'!Join'

    def __init__(
        self,
        how: str,
        order: List[str],
        regions: Dict[str, Region],
    ) -> None:
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


class Assay(yaml.YAMLObject):
    yaml_tag = u'!Assay'

    def __init__(self, name: str, doi: str, description: str,
                 modalities: List[str], lib_struct: str,
                 assay_spec: Dict[str, Region]) -> None:
        self.name = name
        self.doi = doi
        self.description = description
        self.modalities = modalities
        self.lib_struct = lib_struct
        self.assay_spec = assay_spec

    def __repr__(self) -> str:
        d = {
            "name": self.name,
            "doi": self.doi,
            "description": self.description,
            "modalities": self.modalities,
            "lib_struct": self.lib_struct,
            "assay_spec": self.assay_spec,
        }
        return f"{d}"

    def to_JSON(self):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=False,
                          indent=4)

    # note to_yaml is reserved for yaml.YAMLObject
    def to_YAML(self, fname: str):
        with open(fname, 'w') as f:
            yaml.dump(self, f, sort_keys=False)

    def print_sequence(self):
        for name, region in self.assay_spec.items():
            print(region.get_sequence(), end="")
        print("\n", end="")

    def update_spec(self):
        for n, r in self.assay_spec.items():
            r.update_attr()
