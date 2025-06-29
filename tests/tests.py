from seqspec.seqspec import Assay, Join, Region

# sci-rna-sequence
illumina_p5 = Region(
    name="illumina_p5",
    sequence_type="fixed",
    onlist=None,
    sequence="AATGATACGGCGACCACCGAGATCTACAC",
    min_len=29,
    max_len=30,
)

i5 = Region(
    name="i5",
    sequence_type="onlist",
    onlist="i5_onlist.txt",
    sequence="NNNNNNNN",
    min_len=8,
    max_len=9,
)

trusequence_read_1_adapter = Region(
    name="trusequence_read_1_adapter",
    sequence_type="fixed",
    onlist=None,
    sequence="ACACTCTTTCCCTACACGACGCTCTTCCGATCT",
    min_len=33,
    max_len=34,
)

umi = Region(
    name="umi",
    sequence_type="random",
    onlist=None,
    sequence="NNNNNNNN",
    min_len=8,
    max_len=9,
)

cell_bc = Region(
    name="cell_bc",
    sequence_type="onlist",
    onlist="barcodes.txt",
    sequence="NNNNNNNNNNNNNN",
    min_len=14,
    max_len=15,
)

read_1 = Region(
    name="read_1",
    sequence_type="joined",
    join=Join(
        how="union", order=["umi", "cell_bc"], regions={"umi": umi, "cell_bc": cell_bc}
    ),
)

poly_T = Region(
    name="poly_T",
    sequence_type="random",
    onlist=None,
    min_len=1,
    max_len=99,
)

cdna = Region(
    name="cdna",
    sequence_type="random",
    onlist=None,
    min_len=1,
    max_len=99,
)

read_2 = Region(
    name="read_2",
    sequence_type="joined",
    onlist=None,
    join=Join(how="union", order=["cdna"], regions={"cdna": cdna}),
)

ME = Region(
    name="ME",
    sequence_type="fixed",
    sequence="CTGTCTCTTATACACATCT",
    min_len=19,
    max_len=20,
    onlist=None,
)
s7 = Region(
    name="s7",
    sequence_type="fixed",
    sequence="CCGAGCCCACGAGAC",
    min_len=15,
    max_len=16,
    onlist=None,
)

i7_primer = Region(
    name="i7_primer",
    sequence_type="joined",
    onlist=None,
    join=Join(how="union", order=["ME", "s7"], regions={"ME": ME, "s7": s7}),
)

i7 = Region(
    name="i7",
    sequence_type="fixed",
    onlist="i7_onlist.txt",
    sequence="NNNNNNNNNN",
    min_len=10,
    max_len=11,
)

illumina_p7 = Region(
    name="illumina_p7",
    sequence_type="fixed",
    onlist=None,
    sequence="ATCTCGTATGCCGTCTTCTGCTTG",
    min_len=24,
    max_len=25,
)

RNA = Region(
    name="RNA",
    sequence_type="joined",
    join=Join(
        order=[
            "illumina_p5",
            "i5",
            "trusequence_read_1_adapter",
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
            "trusequence_read_1_adapter": trusequence_read_1_adapter,
            "read_1": read_1,
            "poly_T": poly_T,
            "read_2": read_2,
            "i7_primer": i7_primer,
            "i7": i7,
            "illumina_p7": illumina_p7,
        },
    ),
)

assay = Assay(
    assay="sci-RNA-sequence",
    sequencer="Illumina HiSeq 2500",
    name="sci-RNA-sequence/Illumina HiSeq 2500",
    doi="https://doi.org/10.1126/science.aam8940",
    description="combinatorial single-cell RNA-sequence",
    modalities=["RNA"],
    lib_struct="https://teichlab.github.io/scg_lib_structs/methods_html/sci-RNA-sequence.html",  # noqa  # noqa
    library_spec={"RNA": RNA},
)
# assay.print_sequence()
# print(i7_primer.get_len())
# print(i7_primer.get_sequence())

# print(read_1.get_len())
# print(read_1.get_sequence())
# print(read_1.min_len, read_1.max_len)
# print(read_1.sequence)
# assay.to_YAML("test.yaml")
