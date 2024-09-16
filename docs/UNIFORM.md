---
title: Standardize processing
date: 2024-09-07
authors:
  - name: A. Sina Booeshaghi
---

`seqspec` enables uniform preprocessing of sequencing reads.

# Single-cell preprocessing

Single-cell data preprocessing is the procedure where

1. Sequencing reads are aligned to a reference
2. Barcodes errors are corrected
3. UMIs/reads are counted

The goal is to produce a count matrix, where rows are cells or samples and columns are biological features such as genes, proteins, or genomic regions.

There are many tools that perform single-cell RNA-sequencing preprocessing. For this tutorial we will use `kb-python` (which uses `kallisto` and `bustools`), `STARsolo`, `simpleaf` with `seqspec` to perform alignment and quantification. `kb_python` uses `kallisto` to perform read alignment and `bustools` to perform and barcode correction and UMI counting. `STARsolo` performs performs whole genome alignment and barcode error correction. Like `kb-python`, `simpleaf` uses two separate tools under the hood: `alevin` to perform read alignment and `alevin-fry` to perform barcode error correction and UMI counting.

Throughout this tutorial we will use the `dogmaseq-dig` dataset which is a multimodal assay (RNA/ATAC/PROTEIN/TAG). The `seqspec` for this dataset can be found here

## Single-cell/nuclei RNAseq quantification

### `kb-python (kallisto bustools)`

```bash
# standard reference
kb ref -i index.idx -g t2g.txt -f1 transcriptome.fa $(gget ref --ftp -w dna,gtf homo_sapiens)

# seqspec commands to get onlist, technology string, and files
w=$(seqspec onlist -m rna -o onlist.txt -s region-type -i barcode spec.yaml)
x=$(seqspec index -m rna -t kb -s file spec.yaml)
f=$(seqspec file -m rna -s read -f paired -k url spec.yaml  | tr "\t\n" "  ")

# standard quantification
kb count --h5ad -t 16 -m 32G -i index.idx -g t2g.txt -o kb_out -x "$x" -w "$w" "$f"
```

```bash
# spliced, unspliced, ambiguous reference
kb ref --workflow nac \
-i index.idx -g t2g.txt \
-f1 spl.fa -f2 unspl.fa -c1 spl.t2c.txt -c2 unspl.t2c.txt \
$(gget ref --ftp -w dna,gtf homo_sapiens)

# seqspec commands to get onlist, technology string, and files
w=$(seqspec onlist -m rna -o onlist.txt -s region-type -i barcode spec.yaml)
x=$(seqspec index -m rna -t kb -s file spec.yaml)
f=$(seqspec file -m rna -s read -f paired -k url spec.yaml  | tr "\t\n" "  ")

# spliced, unspliced, ambiguous quantification
kb count -t 32 -m 64G -x "$x" -w "$w" -i index.idx -g t2g.txt -c1 spl.t2c.txt -c2 unspl.t2c.txt --h5ad --workflow=nac -o out $f
```

### `STARsolo`

```bash
w=$(seqspec onlist -m rna -r barcode -s region-type spec.yaml)
x=$(seqspec index -m rna -t starsolo -i R1.fastq.gz,R2.fastq.gz spec.yaml)
f=$(seqspec file -m rna -s read -f paired -k url spec.yaml  | tr "\t\n" "  ")

star --soloFeatures Gene --genomeDir index --soloType Droplet --soloCBwhitelist $w $x --readFilesIn $f
```

### `simpleaf`

```bash
mkdir -p ref
# Download reference genome and gene annotations
wget -qO- https://cf.10xgenomics.com/supp/cell-exp/refdata-gex-GRCh38-2020-A.tar.gz | tar xzf - --strip-components=1 -C ./ref

# simpleaf index
simpleaf index \
--output ./out \
--fasta ./ref/fasta/genome.fa \
--gtf ./ref/genes/genes.gtf \
--rlen 91 \
--threads 16 \
--use-piscem  # remove this if missing piscem


w=$(seqspec onlist -m rna -r barcode -s region-type spec.yaml)
x=$(seqspec index -t simpleaf -m rna -i R1.fastq.gz,R2.fastq.gz spec.yaml)

simpleaf quant -r cr-like \
-i index/ -m t2g.txt \
-c "$x" \
-o out/ -x $w \
-1 R1.fastq.gz -2 R2.fastq.gz
```

## Single-cell/nuclei TAG quantification

### `kb-python (kallisto bustools)`

```bash
# build alignment reference
kb ref \
--workflow kite \
-i index.idx \
-g t2g.txt \
-f1 transcriptome.fa \
tag_feature_barcodes.txt

w=$(seqspec onlist -m tag -o onlist.txt -s region-type -i barcode spec.yaml)
x=$(seqspec index -m tag -t kb -s file spec.yaml)
f=$(seqspec file -m tag -s read -f paired -k url spec.yaml  | tr "\t\n" "  ")

# perform alignment, error correction, and counting
kb count \
--workflow kite \
-i index.idx \
-g t2g.txt \
-x $x \
-w $w \
-o out --h5ad -t 2 \
$f
```

## Single-cell/nuclei PROTEIN quantification

### `kb-python (kallisto bustools)`

```bash
# build alignment reference
kb ref \
--workflow kite \
-i index.idx \
-g t2g.txt \
-f1 transcriptome.fa \
protein_feature_barcodes.txt

w=$(seqspec onlist -m protein -o onlist.txt -s region-type -i barcode spec.yaml)
x=$(seqspec index -m protein -t kb -s file spec.yaml)
f=$(seqspec file -m protein -s read -f paired -k url spec.yaml  | tr "\t\n" "  ")

# perform alignment, error correction, and counting
kb count \
--workflow kite \
-i index.idx \
-g t2g.txt \
-x $x \
-w $w \
-o out --h5ad -t 2 \
$f
```

## Single-cell/nuclei CRISPR quantification

Note that single-cell CRISPR guide RNAs can be quantified in the same way as TAG and PROTEIN data. Simply supply the guide RNA barcode file as the “feature barcodes” file.

## Single-cell/nuclei ATAC quantification
