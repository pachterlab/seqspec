---
title: Build a seqspec (simple)
date: 2024-08-19
authors:
  - name: A. Sina Booeshaghi
---

:::{important}
This page is a work in progress. Expect regular updates.
:::

# Overview

We will demonstrate the utility of seqspec by examining the structure of reads generated with the 10xv3 single-cell RNA-seq assay on human PBMCs with short read Illumina sequencing.

https://www.10xgenomics.com/datasets/10k-human-pbmcs-3-ht-v3-1-chromium-x-3-1-high

install seqspec
download the example spec
download the minified reads

# `seqspec` structure

## Assay metadata

Library kit: Dual index (possibly nextera)
Library protocol: Chromium Single Cell 3' Reagent Kits User Guide (v3.1 Chemistry Dual Index) (CG000315 Rev C) using the Chromium X
Sequence kit:

    "NovaSeq 6000 SP Reagent Kit v1.5",
    "NovaSeq 6000 S1 Reagent Kit v1.5",
    "NovaSeq 6000 S2 Reagent Kit v1.5",
    "NovaSeq 6000 S4 Reagent Kit v1.5",

Sequence protocol: Illumina NovaSeq 6000

## Library structure

- Sequence kit primer
- Sample index
- Sequence primer
- Assay structure
  - Barcode
  - UMI
  - polyA
  - cDNA
- Sequence primer
- Sample index
- Sequence kit primer

## Read structure

```
Paired-end, dual indexing Read 1: 28 cycles (16 bp barcode, 12 bp UMI) i5 index: 10 cycles (sample index) i7 index: 10 cycles (sample index) Read 2: 90 cycles (transcript).
```

Read 1 contains the 16bp barcode and 12bp UMI
i5 contains the 10bp sample index
i7 contains the 10bp sample index
Read 2 contains 90bp of the cNDA

FASTQ Files

# `seqspec` tool

## Visualize the spec

## Index the spec
