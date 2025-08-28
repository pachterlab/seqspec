from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, Field, PrivateAttr

from seqspec.Read import Read, ReadInput
from seqspec.Region import Region, RegionInput

from . import __version__


class SeqProtocol(BaseModel):
    protocol_id: Optional[str] = Field(default_factory=lambda: "auto-id")
    name: str
    modality: str


class SeqProtocolInput(BaseModel):
    """
    Input for defining a sequencing protocol metadata entry.

    - `protocol_id`: stable id; defaults to 'auto-id' in `to_seqprotocol()`.
    - `name`: display name of the sequencing protocol.
    - `modality`: modality covered by this protocol (e.g., 'rna').
    """

    protocol_id: Optional[str] = Field(
        default=None,
        description=(
            "Stable identifier for the sequencing protocol; defaults to 'auto-id' if omitted."
        ),
    )
    name: Optional[str] = Field(
        default=None,
        description=("Human-readable name of the sequencing protocol."),
    )
    modality: Optional[str] = Field(
        default=None,
        description=(
            "Modality name associated with the sequencing protocol. Modality must come from the `Assay` modality list."
        ),
    )

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


class SeqKitInput(BaseModel):
    """
    Input for defining a sequencing kit metadata entry.

    - `kit_id`: stable id for the kit.
    - `name`: display name of the kit.
    - `modality`: modality covered by the kit (e.g., 'rna').
    """

    kit_id: Optional[str] = Field(
        default=None,
        description=("Stable identifier for the sequencing kit."),
    )
    name: Optional[str] = Field(
        default=None,
        description=("Human-readable name of the sequencing kit."),
    )
    modality: Optional[str] = Field(
        default=None,
        description=(
            "Modality name associated with the sequencing kit. Modality must come from the `Assay` modality list."
        ),
    )

    def to_seqkit(self) -> SeqKit:
        return SeqKit(
            kit_id=self.kit_id or "", name=self.name, modality=self.modality or ""
        )


class LibProtocol(BaseModel):
    protocol_id: str
    name: str
    modality: str


class LibProtocolInput(BaseModel):
    """
    Input for defining a library protocol metadata entry.

    - `protocol_id`: stable id for the library protocol.
    - `name`: display name of the library protocol.
    - `modality`: modality covered by this protocol (e.g., 'rna').
    """

    protocol_id: Optional[str] = Field(
        default=None,
        description=("Stable identifier for the library protocol."),
    )
    name: Optional[str] = Field(
        default=None,
        description=("Human-readable name of the library protocol."),
    )
    modality: Optional[str] = Field(
        default=None,
        description=(
            "Modality name associated with the library protocol. Modality must come from the `Assay` modality list."
        ),
    )

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


class LibKitInput(BaseModel):
    """
    Input for defining a library kit metadata entry.

    - `kit_id`: stable id for the kit.
    - `name`: display name of the kit.
    - `modality`: modality covered by the kit (e.g., 'rna').
    """

    kit_id: Optional[str] = Field(
        default=None,
        description=("Stable identifier for the library kit."),
    )
    name: Optional[str] = Field(
        default=None,
        description=("Human-readable name of the library kit."),
    )
    modality: Optional[str] = Field(
        default=None,
        description=(
            "Modality name associated with the library kit. Modality must come from the `Assay` modality list."
        ),
    )

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

    # Not part of the public schema; populated when loading from disk.
    _spec_path: Optional[str] = PrivateAttr(default=None)

    def __repr__(self) -> str:
        rds = []
        rgns = []
        for m in self.modalities:
            rds.append(
                f"- {m}: [{', '.join([i.__repr__() for i in self.get_seqspec(m)])}]"
            )
            leaves = self.get_libspec(m).get_leaves()
            lstr = [i.__repr__() for i in leaves]
            rgns.append(f"- {m}: 5'-{'-'.join(lstr)}-3'")
        s = f"""
Assay: {self.assay_id}
Modalities: {self.modalities}
Reads:
{"\n".join(rds)}
Regions:
{"\n".join(rgns)}
"""
        return s

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
        if modality not in self.modalities:
            raise ValueError(f"Modality '{modality}' does not exist")

        target_index = self.modalities.index(modality)

        if target_index >= len(self.library_spec):
            raise ValueError(f"Modality '{modality}' does not exist")

        region = self.library_spec[target_index]
        if getattr(region, "region_id", None) != modality:
            raise ValueError(
                f"Top-level region id '{getattr(region, 'region_id', None)}' does not correspond to modality '{modality}'"
            )

        return region

    def get_seqspec(self, modality):
        return [r for r in self.sequence_spec if r.modality == modality]

    def get_read(self, read_id):
        reads = [r for r in self.sequence_spec if r.read_id == read_id]

        if len(reads) == 0:
            raise IndexError(
                "read_id {} not found in reads {}".format(
                    read_id, [i.read_id for i in self.sequence_spec]
                )
            )
        return reads[0]

    def list_modalities(self):
        return self.modalities

    def insert_regions(
        self, regions: List[Region], modality: str, after: Optional[str] = None
    ) -> None:
        if modality not in self.modalities:
            raise ValueError(f"Modality '{modality}' not found.")
        target_region = self.get_libspec(modality)
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


class AssayInput(BaseModel):
    """
    Input payload for constructing an `Assay` definition.

    Guidance for key fields:
    - `seqspec_version`: fixed by package; rarely overridden.
    - `assay_id`/`name`: stable id and display name for the assay.
    - `doi`/`date`/`description`: metadata describing provenance and context.
    - `modalities`: ordered list of modality names used across specs (e.g., ['rna', 'atac']).
    - `lib_struct`: textual representation of library structure (e.g., a schematic string).

    Protocol/kit fields accept either a string (identifier to external registry) or
    a list of strongly typed inputs defined above.

    Specs:
    - `sequence_spec`: list of `ReadInput` entries (reads) across modalities.
    - `library_spec`: list of top-level `RegionInput` trees, one per modality and in the same order as `modalities`.
    """

    seqspec_version: Optional[str] = Field(
        default=__version__,
        description=("Version of the seqspec schema used to construct this assay."),
    )
    assay_id: Optional[str] = Field(
        default=None,
        description=("Stable identifier for the assay definition."),
    )
    name: Optional[str] = Field(
        default=None,
        description=("Human-readable assay name."),
    )
    doi: Optional[str] = Field(
        default=None,
        description=("DOI or accession describing the assay or reference publication."),
    )
    date: Optional[str] = Field(
        default=None,
        description=("Date string (e.g., YYYY-MM-DD) for the assay definition or run."),
    )
    description: Optional[str] = Field(
        default=None,
        description=("Free text description of the assay."),
    )
    modalities: Optional[List[str]] = Field(
        default=None,
        description=(
            "Ordered list of modality names used in this assay (e.g., ['rna', 'atac'])."
        ),
    )
    lib_struct: Optional[str] = Field(
        default=None,
        description=(
            "String diagram of the library structure (for display or shorthand)."
        ),
    )

    sequence_protocol: Union[str, List[SeqProtocolInput], None] = Field(
        default=None,
        description=(
            "Either a registry identifier (string) or a list of `SeqProtocolInput`."
        ),
    )
    sequence_kit: Union[str, List[SeqKitInput], None] = Field(
        default=None,
        description=(
            "Either a registry identifier (string) or a list of `SeqKitInput`."
        ),
    )
    library_protocol: Union[str, List[LibProtocolInput], None] = Field(
        default=None,
        description=(
            "Either a registry identifier (string) or a list of `LibProtocolInput`."
        ),
    )
    library_kit: Union[str, List[LibKitInput], None] = Field(
        default=None,
        description=(
            "Either a registry identifier (string) or a list of `LibKitInput`."
        ),
    )

    sequence_spec: Optional[List[ReadInput]] = Field(
        default=None,
        description=(
            "List of read definitions across modalities. Must be a list of `Read` objects"
        ),
    )
    library_spec: Optional[List[RegionInput]] = Field(
        default=None,
        description=(
            "List of top-level region trees (one per modality, same order as `modalities`). Must be a list of `Region` objects."
        ),
    )

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
