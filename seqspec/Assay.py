import yaml
from seqspec.Region import Region, Read
from typing import List, Optional, Union
import json
from . import __version__


class Assay(yaml.YAMLObject):
    yaml_tag = "!Assay"

    def __init__(
        self,
        assay_id: str,
        name: str,
        doi: str,
        date: str,
        description: str,
        modalities: List[str],
        lib_struct: str,
        sequence_protocol: Union[str, List["SeqProtocol"], None],
        sequence_kit: Union[str, List["SeqKit"], None],
        library_protocol: Union[str, List["LibProtocol"], None],
        library_kit: Union[str, List["LibKit"], None],
        sequence_spec: List[Read],
        library_spec: List[Region],
        seqspec_version: str = __version__,
    ) -> None:
        super().__init__()
        self.seqspec_version = seqspec_version
        self.assay_id = assay_id
        self.name = name
        self.doi = doi
        self.date = date
        self.description = description
        self.modalities = modalities
        self.lib_struct = lib_struct
        self.sequence_protocol = sequence_protocol
        self.sequence_kit = sequence_kit
        self.library_protocol = library_protocol
        self.library_kit = library_kit
        self.sequence_spec = sequence_spec
        self.library_spec = library_spec

    def __repr__(self) -> str:
        d = {
            "seqspec_version": self.seqspec_version,
            "assay_id": self.assay_id,
            "name": self.name,
            "doi": self.doi,
            "date": self.date,
            "description": self.description,
            "modalities": self.modalities,
            "lib_struct": self.lib_struct,
            "sequence_protocol": self.sequence_protocol,
            "sequence_kit": self.sequence_kit,
            "library_protocol": self.library_protocol,
            "library_kit": self.library_kit,
            "sequence_spec": self.sequence_spec,
            "library_spec": self.library_spec,
        }
        return f"{d}"

    def to_dict(self):
        if isinstance(self.sequence_kit, list):
            sequence_kit = [o.to_dict() for o in self.sequence_kit]
        else:
            sequence_kit = self.sequence_kit

        if isinstance(self.sequence_protocol, list):
            sequence_protocol = [o.to_dict() for o in self.sequence_protocol]
        else:
            sequence_protocol = self.sequence_protocol

        if isinstance(self.library_kit, list):
            library_kit = [o.to_dict() for o in self.library_kit]
        else:
            library_kit = self.library_kit

        if isinstance(self.library_protocol, list):
            library_protocol = [o.to_dict() for o in self.library_protocol]
        else:
            library_protocol = self.library_protocol

        d = {
            "seqspec_version": self.seqspec_version,
            "assay_id": self.assay_id,
            "name": self.name,
            "doi": self.doi,
            "date": self.date,
            "description": self.description,
            "modalities": self.modalities,
            "lib_struct": self.lib_struct,
            "sequence_protocol": sequence_protocol,
            "sequence_kit": sequence_kit,
            "library_protocol": library_protocol,
            "library_kit": library_kit,
            "sequence_spec": [o.to_dict() for o in self.sequence_spec],
            "library_spec": [o.to_dict() for o in self.library_spec],
        }

        return d

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)

    # note to_yaml is reserved for yaml.YAMLObject
    def to_YAML(self, fname: Optional[str] = None):
        """Export seqspec to yaml

        If fname is provided, the seqspec text will be written to the
        file.
        If fname is None, the seqspec text will be returned as a string.
        """
        if fname is None:
            return yaml.dump(self, sort_keys=False)
        else:
            with open(fname, "w") as f:
                yaml.dump(self, f, sort_keys=False)

    def print_sequence(self):
        for region in self.library_spec:
            print(region.get_sequence(), end="")
        print("\n", end="")

    def update_spec(self):
        for r in self.library_spec:
            r.update_attr()

    def get_libspec(self, modality) -> Region:
        return self.library_spec[self.modalities.index(modality)]

    def get_seqspec(self, modality):
        return [r for r in self.sequence_spec if r.modality == modality]

    def get_read(self, read_id):
        return [r for r in self.sequence_spec if r.read_id == read_id][0]

    def list_modalities(self):
        return self.modalities


class SeqProtocol(yaml.YAMLObject):
    yaml_tag = "!SeqProtocol"

    def __init__(self, name: str, modality: str) -> None:
        self.protocol_id = id
        self.name = name
        self.modality = modality

    def __repr__(self) -> str:
        d = {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "modality": self.modality,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "modality": self.modality,
        }
        return d


class SeqKit(yaml.YAMLObject):
    yaml_tag = "!SeqKit"

    def __init__(self, kit_id: str, name: str, modality: str) -> None:
        self.kit_id = kit_id
        self.name = name
        self.modality = modality

    def __repr__(self) -> str:
        d = {
            "kit_id": self.kit_id,
            "name": self.name,
            "modality": self.modality,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "kit_id": self.kit_id,
            "name": self.name,
            "modality": self.modality,
        }
        return d


class LibProtocol(yaml.YAMLObject):
    yaml_tag = "!LibProtocol"

    def __init__(
        self, protocol_id: str, name: str, description: str, modality: str
    ) -> None:
        self.protocol_id = protocol_id
        self.name = name
        self.modality = modality

    def __repr__(self) -> str:
        d = {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "modality": self.modality,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "modality": self.modality,
        }
        return d


class LibKit(yaml.YAMLObject):
    yaml_tag = "!LibKit"

    def __init__(self, kit_id: str, name: str, modality: str) -> None:
        self.kit_id = kit_id
        self.name = name
        self.modality = modality

    def __repr__(self) -> str:
        d = {
            "kit_id": self.kit_id,
            "name": self.name,
            "modality": self.modality,
        }
        return f"{d}"

    def to_dict(self):
        d = {
            "kit_id": self.kit_id,
            "name": self.name,
            "modality": self.modality,
        }
        return d
