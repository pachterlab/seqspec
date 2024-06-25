# Using seqspec effectively

A `seqspec` file provides complete information about the structure of a sequencing library and seqeuencing reads generated from it. Herein we document common tasks that users may find useful when working with `seqspec` files. In this document we will work with the `examples/specs/SPLiT-seq/spec.yaml` file. In some cases we will use the command line tool `jq` to extract relevant information from the `seqspec` tool output though this is not required.

What modalities are annotated in my spec?

```bash
$ seqspec info -k modalities spec.yaml
rna
```

What library kits/protocols and sequencing kit/protocols were used to generated the library?

```bash
$ seqspec info -f json -k meta spec.yaml
{
    "seqspec_version": "0.2.0",
    "assay_id": "SPLiTSeq",
    "name": "SPLiTSeq",
    "doi": "https://doi.org/10.1126/science.aam8999",
    "date": "15 March 2018",
    "description": "split-pool ligation-based transcriptome sequencing",
    "lib_struct": "https://teichlab.github.io/scg_lib_structs/methods_html/SPLiT-seq.html",
    "sequence_protocol": "NextSeq 500",
    "sequence_kit": "NextSeq 550 reagents",
    "library_protocol": "SPLiTSeq RNA",
    "library_kit": "Custom/Nextera/Truseq Single Index"
}
```

What are the sequencing reads annotated in my spec?

```bash
$ seqspec info -k sequence_spec spec.yaml
rna     R1.fastq.gz     pos     140     140     Read_1_primer   Read 1
rna     I1.fastq.gz     pos     6       6       Read_2_primer   Index 1 (i7 index)
rna     R2.fastq.gz     neg     86      86      Read_2_primer   Read 2
```

What does my sequencing library look like?

```bash
seqspec info -k library_spec spec.yaml
rna     P5      illumina_p5     P5      fixed   AATGATACGGCGACCACCGAGATCTACAC   29      29      None
rna     Spacer  linker  Spacer  fixed   TAGATCGC        8       8       None
rna     Read_1_primer   read1_primer    Read_1_primer   fixed   TCGTCGGCAGCGTCAGATGTGTATAAGAGACAG       33      33      None
rna     cDNA    cdna    cDNA    random  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    1      100      None
rna     RT_primer       primer  RT_primer       onlist  NNNNNNNNNNNNNNN 6       15      onlist_rt_primer.txt
rna     Round_1_BC      barcode Round_1_BC      onlist  NNNNNNNN        8       8       onlist_round1.txt
rna     linker_1        linker  linker_1        fixed   GCTTACGAGACCGGAGAGTTCGTGCACCTA  30      30      None
rna     Round_2_BC      barcode Round_2_BC      onlist  NNNNNNNN        8       8       onlist_round1.txt
rna     Linker_2        linker  Linker_2        fixed   TCAGCATGCGGCTACGCTTTGTAGCCGGTG  30      30      None
rna     Round_3_BC      barcode Round_3_BC      onlist  NNNNNNNN        8       8       onlist_round1.txt
rna     UMI     umi     UMI     random  XXXXXXXXXX      10      10      onlist_round2.txt
rna     Read_2_primer   primer  Read_2_primer   fixed   TCTAGCCTTCTCGTGTGCAGAC  22      22      onlist_round3.txt
rna     Round_4_BC      barcode Round_4_BC      onlist  NNNNNN  6       6       onlist_round4.txt
rna     P7      illumina_p7     P7      fixed   ATCTCGTATGCCGTCTTCTGCTTG        24      24      None
```

Which library elements are contained in my sequencing reads?
Using the tables above we specify the sequencing read and the associated modality.

````bash
$ seqspec index -m rna -r "R1.fastq.gz" spec.yaml
R1.fastq.gz     cDNA    cdna    0       100
R1.fastq.gz     RT_primer       primer  100     115
R1.fastq.gz     Round_1_BC      barcode 115     123
R1.fastq.gz     linker_1        linker  123     140

```bash
$ seqspec index -m rna -r "R2.fastq.gz" spec.yaml
R2.fastq.gz     UMI     umi     0       10
R2.fastq.gz     Round_3_BC      barcode 10      18
R2.fastq.gz     Linker_2        linker  18      48
R2.fastq.gz     Round_2_BC      barcode 48      56
R2.fastq.gz     linker_1        linker  56      86
````

```bash
$ seqspec index -m rna -r "I1.fastq.gz" spec.yaml
I1.fastq.gz     Round_4_BC      barcode 0       6
```
