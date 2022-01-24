from enum import Enum
from typing import Optional, List
import yaml


class SeqType(Enum):
    FIXED = "fixed"
    RANDOM = "random"
    ONLIST = "onlist"
    JOINED = "joined"


class Region:
    def __init__(self,
                 name: str,
                 seq_type: str,
                 seq: Optional[str] = None,
                 min_len: Optional[int] = None,
                 max_len: Optional[int] = None,
                 onlist: Optional[str] = None,
                 join: Optional['Join'] = None) -> None:
        self.name = name
        self.seq_type = SeqType[seq_type.upper()].value
        self.seq = seq

        self.min_len = min_len
        self.max_len = max_len

        self.onlist = onlist
        self.join = join

    def __repr__(self) -> str:
        d = {
            self.name: {
                "seq_type": self.seq_type,
                "onlist": self.onlist,
                "seq": self.seq,
                "min_len": self.min_len,
                "max_len": self.max_len,
                "join": self.join
            }
        }
        return f"{d}"


class Join:
    def __init__(
        self,
        how: str,
        order: List[str],
        regions: List[Region],
    ) -> None:
        self.regions = {i.name: i for i in regions}
        self.how = how
        self.order = order

    def __repr__(self) -> str:
        d = {
            "how": self.how,
            "order": self.order,
            "regions": self.regions,
        }
        return f"{d}"


# sci-rna-seq
p5 = Region(name="p5",
            seq_type="fixed",
            onlist=None,
            seq="AATGATACGGCGACCACCGAGATCTACAC",
            min_len=29,
            max_len=30)

i1 = Region(name="i1",
            seq_type="onlist",
            onlist="index1.txt",
            seq="NNNNNNNN",
            min_len=8,
            max_len=9)

r1_adapter = Region(name="r1_adapter",
                    seq_type="fixed",
                    onlist=None,
                    seq="ACACTCTTTCCCTACACGACGCTCTTCCGATCT",
                    min_len=33,
                    max_len=34)

cdna = Region(name="cdna",
              seq_type="random",
              onlist=None,
              seq=None,
              min_len=1,
              max_len=99)

umi = Region(name="umi",
             seq_type="random",
             onlist=None,
             seq="NNNNNNNNNN",
             min_len=10,
             max_len=11)

r2_adapter = Region(name="r2_adapter",
                    seq_type="fixed",
                    onlist=None,
                    seq="AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC",
                    min_len=34,
                    max_len=35)

cell_bc = Region(name="cell_bc",
                 seq_type="onlist",
                 onlist="barcodes.txt",
                 seq="NNNNNNNNNNNNNN",
                 min_len=14,
                 max_len=15)

p7 = Region(name="p7",
            seq_type="fixed",
            onlist=None,
            seq="ATCTCGTATGCCGTCTTCTGCTTG",
            min_len=24,
            max_len=25)

assay = Region(
    name="sci-RNA-seq",
    seq_type="joined",
    join=Join(
        order=["as"],
        how="union",
        regions=[p5, i1, r1_adapter, cdna, umi, r2_adapter, cell_bc, p7],
    ))

print(yaml.dump(assay))
