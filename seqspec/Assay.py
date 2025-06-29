from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, Field

from seqspec.llmtools import LLMInput
from seqspec.Read import Read, ReadInput
from seqspec.Region import Region, RegionInput

from . import __version__


class SeqProtocol(BaseModel):
    protocol_id: Optional[str] = Field(default_factory=lambda: "auto-id")
    name: str
    modality: str

    def to_dict(self):
        return self.model_dump()


class SeqProtocolInput(LLMInput):
    protocol_id: Optional[str] = None
    name: Optional[str] = None
    modality: Optional[str] = None

    def to_seqprotocol(self) -> SeqProtocol:
        return SeqProtocol(
            protocol_id=self.protocol_id or "auto-id",
            name=self.name or "",
            modality=self.modality or "",
        )


class SeqKit(BaseModel):
    kit_id: str
    name: Optional[str]
    modality: str

    def to_dict(self):
        return self.model_dump()


class SeqKitInput(LLMInput):
    kit_id: Optional[str] = None
    name: Optional[str] = None
    modality: Optional[str] = None

    def to_seqkit(self) -> SeqKit:
        return SeqKit(
            kit_id=self.kit_id or "", name=self.name, modality=self.modality or ""
        )


class LibProtocol(BaseModel):
    protocol_id: str
    name: str
    modality: str

    def to_dict(self):
        return self.model_dump()


class LibProtocolInput(LLMInput):
    protocol_id: Optional[str] = None
    name: Optional[str] = None
    modality: Optional[str] = None

    def to_libprotocol(self) -> LibProtocol:
        return LibProtocol(
            protocol_id=self.protocol_id or "",
            name=self.name or "",
            modality=self.modality or "",
        )


class LibKit(BaseModel):
    kit_id: str
    name: Optional[str]
    modality: str

    def to_dict(self):
        return self.model_dump()


class LibKitInput(LLMInput):
    kit_id: Optional[str] = None
    name: Optional[str] = None
    modality: Optional[str] = None

    def to_libkit(self) -> LibKit:
        return LibKit(
            kit_id=self.kit_id or "", name=self.name, modality=self.modality or ""
        )


class Assay(BaseModel):
    seqspec_version: Optional[str] = __version__
    assay_id: str
    name: str
    doi: str
    date: str
    description: str
    modalities: List[str]
    lib_struct: str

    sequence_protocol: Union[str, List[SeqProtocol], None]
    sequence_kit: Union[str, List[SeqKit], None]
    library_protocol: Union[str, List[LibProtocol], None]
    library_kit: Union[str, List[LibKit], None]

    sequence_spec: List[Read]
    library_spec: List[Region]

    def __repr__(self) -> str:
        return str(self.model_dump())

    def to_dict(self):
        return self.model_dump()

    def to_JSON(self):
        return self.model_dump_json(indent=4)

    def to_YAML(self, fname: Optional[str] = None):
        yaml_str = yaml.dump(self.model_dump(), sort_keys=False)
        if fname is None:
            return yaml_str
        else:
            with open(fname, "w") as f:
                f.write(yaml_str)

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

    def insert_regions(
        self, regions: List[Region], modality: str, after: Optional[str] = None
    ) -> None:
        if modality not in self.modalities:
            raise ValueError(f"Modality '{modality}' not found.")
        target_region = self.get_libspec(modality)
        if target_region.regions is None:
            target_region.regions = []
        insert_idx = 0
        if after:
            for idx, r in enumerate(target_region.regions):
                if r.region_id == after:
                    insert_idx = idx + 1
                    break
            else:
                raise ValueError(
                    f"No region with id '{after}' found under modality '{modality}'"
                )
        for region in regions:
            region.parent_id = target_region.region_id
            target_region.regions.insert(insert_idx, region)
            insert_idx += 1
        target_region.update_attr()

    def insert_reads(
        self, reads: List[Read], modality: str, after: Optional[str] = None
    ) -> None:
        if modality not in self.modalities:
            raise ValueError(f"Modality '{modality}' not found.")

        # Find insertion index
        insert_idx = len(self.sequence_spec)
        if after is not None:
            for idx, read in enumerate(self.sequence_spec):
                if read.read_id == after:
                    insert_idx = idx + 1
                    break
        else:
            insert_idx = 0

        # Insert reads at the specified position
        for read in reads:
            read.modality = modality
            self.sequence_spec.insert(insert_idx, read)
            insert_idx += 1


class AssayInput(LLMInput):
    seqspec_version: Optional[str] = __version__
    assay_id: Optional[str] = None
    name: Optional[str] = None
    doi: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    modalities: Optional[List[str]] = None
    lib_struct: Optional[str] = None

    sequence_protocol: Union[str, List[SeqProtocolInput], None] = None
    sequence_kit: Union[str, List[SeqKitInput], None] = None
    library_protocol: Union[str, List[LibProtocolInput], None] = None
    library_kit: Union[str, List[LibKitInput], None] = None

    sequence_spec: Optional[List[ReadInput]] = None
    library_spec: Optional[List[RegionInput]] = None

    def to_assay(self) -> Assay:
        return Assay(
            seqspec_version=self.seqspec_version,
            assay_id=self.assay_id or "",
            name=self.name or "",
            doi=self.doi or "",
            date=self.date or "",
            description=self.description or "",
            modalities=self.modalities or [],
            lib_struct=self.lib_struct or "",
            sequence_protocol=(
                self.sequence_protocol
                if isinstance(self.sequence_protocol, str)
                else [sp.to_seqprotocol() for sp in self.sequence_protocol or []]
            ),
            sequence_kit=(
                self.sequence_kit
                if isinstance(self.sequence_kit, str)
                else [sk.to_seqkit() for sk in self.sequence_kit or []]
            ),
            library_protocol=(
                self.library_protocol
                if isinstance(self.library_protocol, str)
                else [lp.to_libprotocol() for lp in self.library_protocol or []]
            ),
            library_kit=(
                self.library_kit
                if isinstance(self.library_kit, str)
                else [lk.to_libkit() for lk in self.library_kit or []]
            ),
            sequence_spec=[r.to_read() for r in self.sequence_spec or []],
            library_spec=[r.to_region() for r in self.library_spec or []],
        )


# import yaml
# from seqspec.Region import Region
# from seqspec.Read import Read
# from typing import List, Optional, Union
# import json
# from . import __version__


# class Assay(yaml.YAMLObject):
#     yaml_tag = "!Assay"

#     def __init__(
#         self,
#         assay_id: str,
#         name: str,
#         doi: str,
#         date: str,
#         description: str,
#         modalities: List[str],
#         lib_struct: str,
#         sequence_protocol: Union[str, List["SeqProtocol"], None],
#         sequence_kit: Union[str, List["SeqKit"], None],
#         library_protocol: Union[str, List["LibProtocol"], None],
#         library_kit: Union[str, List["LibKit"], None],
#         sequence_spec: List[Read],
#         library_spec: List[Region],
#         seqspec_version: str = __version__,
#     ) -> None:
#         super().__init__()
#         self.seqspec_version = seqspec_version
#         self.assay_id = assay_id
#         self.name = name
#         self.doi = doi
#         self.date = date
#         self.description = description
#         self.modalities = modalities
#         self.lib_struct = lib_struct
#         self.sequence_protocol = sequence_protocol
#         self.sequence_kit = sequence_kit
#         self.library_protocol = library_protocol
#         self.library_kit = library_kit
#         self.sequence_spec = sequence_spec
#         self.library_spec = library_spec

#     def __repr__(self) -> str:
#         d = {
#             "seqspec_version": self.seqspec_version,
#             "assay_id": self.assay_id,
#             "name": self.name,
#             "doi": self.doi,
#             "date": self.date,
#             "description": self.description,
#             "modalities": self.modalities,
#             "lib_struct": self.lib_struct,
#             "sequence_protocol": self.sequence_protocol,
#             "sequence_kit": self.sequence_kit,
#             "library_protocol": self.library_protocol,
#             "library_kit": self.library_kit,
#             "sequence_spec": self.sequence_spec,
#             "library_spec": self.library_spec,
#         }
#         return f"{d}"

#     def to_dict(self):
#         if isinstance(self.sequence_kit, list):
#             sequence_kit = [o.to_dict() for o in self.sequence_kit]
#         else:
#             sequence_kit = self.sequence_kit

#         if isinstance(self.sequence_protocol, list):
#             sequence_protocol = [o.to_dict() for o in self.sequence_protocol]
#         else:
#             sequence_protocol = self.sequence_protocol

#         if isinstance(self.library_kit, list):
#             library_kit = [o.to_dict() for o in self.library_kit]
#         else:
#             library_kit = self.library_kit

#         if isinstance(self.library_protocol, list):
#             library_protocol = [o.to_dict() for o in self.library_protocol]
#         else:
#             library_protocol = self.library_protocol

#         d = {
#             "seqspec_version": self.seqspec_version,
#             "assay_id": self.assay_id,
#             "name": self.name,
#             "doi": self.doi,
#             "date": self.date,
#             "description": self.description,
#             "modalities": self.modalities,
#             "lib_struct": self.lib_struct,
#             "sequence_protocol": sequence_protocol,
#             "sequence_kit": sequence_kit,
#             "library_protocol": library_protocol,
#             "library_kit": library_kit,
#             "sequence_spec": [o.to_dict() for o in self.sequence_spec],
#             "library_spec": [o.to_dict() for o in self.library_spec],
#         }

#         return d

#     def to_JSON(self):
#         return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)

#     # note to_yaml is reserved for yaml.YAMLObject
#     def to_YAML(self, fname: Optional[str] = None):
#         """Export seqspec to yaml

#         If fname is provided, the seqspec text will be written to the
#         file.
#         If fname is None, the seqspec text will be returned as a string.
#         """
#         if fname is None:
#             return yaml.dump(self, sort_keys=False)
#         else:
#             with open(fname, "w") as f:
#                 yaml.dump(self, f, sort_keys=False)

#     def print_sequence(self):
#         for region in self.library_spec:
#             print(region.get_sequence(), end="")
#         print("\n", end="")

#     def update_spec(self):
#         for r in self.library_spec:
#             r.update_attr()

#     def get_libspec(self, modality) -> Region:
#         return self.library_spec[self.modalities.index(modality)]

#     def get_seqspec(self, modality):
#         return [r for r in self.sequence_spec if r.modality == modality]

#     def get_read(self, read_id):
#         return [r for r in self.sequence_spec if r.read_id == read_id][0]

#     def list_modalities(self):
#         return self.modalities

#     def insert_regions(self, regions: List[Region], modality: str, after: Optional[str] = None) -> None:
#         """Insert Regions into the library specification for a given modality.

#         Parameters
#         ----------
#         regions : List[Region]
#             The Region objects to insert.
#         modality : str
#             The modality whose library specification the regions belong to.
#         after : Optional[str], default None
#             If provided, the *region_id* of an existing child Region of the
#             modality root after which the new regions should be inserted. If
#             ``None`` (default), the regions are prepended to the beginning of
#             the child list.

#         Raises
#         ------
#         ValueError
#             If *modality* is not found in the assay or if *after* is provided
#             but no child Region with a matching ``region_id`` exists.
#         """
#         # Validate modality exists
#         if modality not in self.modalities:
#             raise ValueError(
#                 f"Modality '{modality}' not found. Available modalities: {', '.join(self.modalities)}"
#             )

#         # Retrieve the top-level (meta) Region for this modality
#         target_region = self.get_libspec(modality)

#         # Ensure that the modality root has a list to hold child regions
#         if target_region.regions is None:
#             target_region.regions = []

#         # Determine insertion index
#         if after is None:
#             # Prepend at the beginning
#             insert_idx = 0
#         else:
#             # Find the index of the Region with region_id == after
#             insert_idx = None
#             for idx, r in enumerate(target_region.regions):
#                 if r.region_id == after:
#                     insert_idx = idx + 1  # insert *after* this index
#                     break
#             if insert_idx is None:
#                 raise ValueError(
#                     f"Region with region_id '{after}' not found among children of modality '{modality}'."
#                 )

#         # Insert and update parents for each region
#         for region in regions:
#             region.parent_id = target_region.region_id
#             target_region.regions.insert(insert_idx, region)
#             insert_idx += 1  # Increment index for next region

#         # Update lengths and sequences recursively so the spec stays consistent
#         target_region.update_attr()
#         return

#     def insert_reads(self, reads: List[Read], modality: str) -> None:
#         """Insert Read objects into the sequence specification for a given modality.

#         Parameters
#         ----------
#         reads : List[Read]
#             The Read objects to insert.
#         modality : str
#             The modality whose sequence specification the reads belong to.

#         Raises
#         ------
#         ValueError
#             If *modality* is not found in the assay.
#         """
#         # Validate modality exists
#         if modality not in self.modalities:
#             raise ValueError(
#                 f"Modality '{modality}' not found. Available modalities: {', '.join(self.modalities)}"
#             )

#         # Set the modality for each read and add to sequence_spec
#         for read in reads:
#             read.modality = modality
#             self.sequence_spec.append(read)

#         return


# class SeqProtocol(yaml.YAMLObject):
#     yaml_tag = "!SeqProtocol"

#     def __init__(self, name: str, modality: str) -> None:
#         self.protocol_id = id
#         self.name = name
#         self.modality = modality

#     def __repr__(self) -> str:
#         d = {
#             "protocol_id": self.protocol_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return f"{d}"

#     def to_dict(self):
#         d = {
#             "protocol_id": self.protocol_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return d


# class SeqKit(yaml.YAMLObject):
#     yaml_tag = "!SeqKit"

#     def __init__(self, kit_id: str, name: str, modality: str) -> None:
#         self.kit_id = kit_id
#         self.name = name
#         self.modality = modality

#     def __repr__(self) -> str:
#         d = {
#             "kit_id": self.kit_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return f"{d}"

#     def to_dict(self):
#         d = {
#             "kit_id": self.kit_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return d


# class LibProtocol(yaml.YAMLObject):
#     yaml_tag = "!LibProtocol"

#     def __init__(
#         self, protocol_id: str, name: str, description: str, modality: str
#     ) -> None:
#         self.protocol_id = protocol_id
#         self.name = name
#         self.modality = modality

#     def __repr__(self) -> str:
#         d = {
#             "protocol_id": self.protocol_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return f"{d}"

#     def to_dict(self):
#         d = {
#             "protocol_id": self.protocol_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return d


# class LibKit(yaml.YAMLObject):
#     yaml_tag = "!LibKit"

#     def __init__(self, kit_id: str, name: str, modality: str) -> None:
#         self.kit_id = kit_id
#         self.name = name
#         self.modality = modality

#     def __repr__(self) -> str:
#         d = {
#             "kit_id": self.kit_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return f"{d}"

#     def to_dict(self):
#         d = {
#             "kit_id": self.kit_id,
#             "name": self.name,
#             "modality": self.modality,
#         }
#         return d
