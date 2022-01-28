from typing import Optional, List, Dict
import yaml
import json


# todo figure out how to do enums type options
class Region(yaml.YAMLObject):
    yaml_tag = u'!Region'

    def __init__(self,
                 name: str,
                 seq_type: str,
                 seq: Optional[str] = None,
                 min_len: Optional[int] = None,
                 max_len: Optional[int] = None,
                 onlist: Optional[str] = None,
                 join: Optional['Join'] = None) -> None:
        self.name = name
        self.seq_type = seq_type
        self.seq = seq

        self.min_len = min_len
        self.max_len = max_len

        self.onlist = onlist
        self.join = join

    def printSeq(self):
        if self.join:
            for n, r in self.join.regions.items():
                r.printSeq()
        else:
            if self.seq:
                return print(self.seq, end="")
            elif self.seq is None:
                return print("X", end="")

    def __repr__(self) -> str:
        d = {
            "seq_type": self.seq_type,
            "onlist": self.onlist,
            "seq": self.seq,
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

    def toJSON(self):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=False,
                          indent=4)

    def toYAML(self, fname: str):
        with open(fname, 'w') as f:
            yaml.dump(self, f, sort_keys=False)

    def printSpec(self):
        for name, region in self.assay_spec.items():
            region.printSeq()


# sci-rna-seq
illumina_p5 = Region(name="illumina_p5",
                     seq_type="fixed",
                     onlist=None,
                     seq="AATGATACGGCGACCACCGAGATCTACAC",
                     min_len=29,
                     max_len=30,
                     join=None)

i5 = Region(name="i5",
            seq_type="onlist",
            onlist="i5_onlist.txt",
            seq="NNNNNNNN",
            min_len=8,
            max_len=9,
            join=None)

truseq_read_1_adapter = Region(name="truseq_read_1_adapter",
                               seq_type="fixed",
                               onlist=None,
                               seq="ACACTCTTTCCCTACACGACGCTCTTCCGATCT",
                               min_len=33,
                               max_len=34,
                               join=None)

umi = Region(name="umi",
             seq_type="random",
             onlist=None,
             seq="NNNNNNNN",
             min_len=8,
             max_len=9,
             join=None)

cell_bc = Region(name="cell_bc",
                 seq_type="onlist",
                 onlist="barcodes.txt",
                 seq="NNNNNNNNNNNNNN",
                 min_len=14,
                 max_len=15)

read_1 = Region(name="read_1",
                seq_type="joined",
                seq=None,
                min_len=None,
                max_len=None,
                join=Join(how="union",
                          order=["umi", "cell_bc"],
                          regions={
                              "umi": umi,
                              "cell_bc": cell_bc
                          }))

poly_T = Region(name="poly_T",
                seq_type="random",
                onlist=None,
                seq=None,
                min_len=1,
                max_len=99,
                join=None)

cdna = Region(name="cdna",
              seq_type="random",
              onlist=None,
              seq=None,
              min_len=1,
              max_len=99,
              join=None)

read_2 = Region(name="read_2",
                seq_type="joined",
                onlist=None,
                min_len=None,
                max_len=None,
                join=Join(how="union", order=["cdna"], regions={"cdna": cdna}))

ME = Region(name="ME",
            seq_type="fixed",
            seq="CTGTCTCTTATACACATCT",
            min_len=19,
            max_len=20,
            onlist=None,
            join=None)
s7 = Region(name="s7",
            seq_type="fixed",
            seq="CCGAGCCCACGAGAC",
            min_len=15,
            max_len=16,
            onlist=None,
            join=None)

i7_primer = Region(name="i7_primer",
                   seq_type="joined",
                   seq=None,
                   min_len=None,
                   max_len=None,
                   onlist=None,
                   join=Join(how="union",
                             order=["ME", "s7"],
                             regions={
                                 "ME": ME,
                                 "s7": s7
                             }))

i7 = Region(name="i7",
            seq_type="fixed",
            onlist="i7_onlist.txt",
            seq="NNNNNNNNNN",
            min_len=10,
            max_len=11)

illumina_p7 = Region(name="illumina_p7",
                     seq_type="fixed",
                     onlist=None,
                     seq="ATCTCGTATGCCGTCTTCTGCTTG",
                     min_len=24,
                     max_len=25)

RNA = Region(name="RNA",
             seq_type="joined",
             join=Join(
                 order=[
                     "illumina_p5",
                     "i5",
                     "truseq_read_1_adapter",
                     "read_1",
                     "read_2",
                     "i7_primer",
                     "i7",
                     "illumina_p7",
                 ],
                 how="union",
                 regions={
                     "illumina_p5": illumina_p5,
                     "i5": i5,
                     "truseq_read_1_adapter": truseq_read_1_adapter,
                     "read_1": read_1,
                     "read_2": read_2,
                     "i7_primer": i7_primer,
                     "i7": i7,
                     "illumina_p7": illumina_p7
                 },
             ))

assay = Assay(
    name="sci-RNA-seq",
    doi="https://doi.org/10.1126/science.aam8940",
    description="combinatorial single-cell RNA-seq",
    modalities=["RNA"],
    lib_struct=  # noqa
    "https://teichlab.github.io/scg_lib_structs/methods_html/sci-RNA-seq.html",
    assay_spec={"RNA": RNA})

# i7_primer.printSeq()
# assay.printSpec()

assay.toYAML("spec.yaml")
with open("spec.yaml", 'r') as stream:
    data_loaded: Assay = yaml.load(stream, Loader=yaml.Loader)
data_loaded.printSpec()
