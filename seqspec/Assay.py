import yaml
from seqspec.Region import Region
from typing import List
import json


class Assay(yaml.YAMLObject):
    yaml_tag = "!Assay"

    def __init__(
        self,
        name: str,
        doi: str,
        description: str,
        modalities: List[str],
        lib_struct: str,
        assay_spec: List[Region],
    ) -> None:
        super().__init__()
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

    def to_dict(self):
        d = {
            "name": self.name,
            "doi": self.doi,
            "description": self.description,
            "modalities": self.modalities,
            "lib_struct": self.lib_struct,
            "assay_spec": [o.to_dict() for o in self.assay_spec],
        }
        return d

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)

    # note to_yaml is reserved for yaml.YAMLObject
    def to_YAML(self, fname: str):
        with open(fname, "w") as f:
            yaml.dump(self, f, sort_keys=False)

    def print_sequence(self):
        for region in self.assay_spec:
            print(region.get_sequence(), end="")
        print("\n", end="")

    def update_spec(self):
        for r in self.assay_spec:
            r.update_attr()
