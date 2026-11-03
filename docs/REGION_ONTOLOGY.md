---
title: Region Ontology
---

# Region Ontology

Seqspec describes the designed structure of a sequencing assay. A region annotation should describe what a sequence interval is intended to do under perfect measurement. Data validation tools can then check whether observed reads match that design.

This document drafts a region ontology for seqspec. The goal is to make `region_type` machine-readable while preserving current labels such as `barcode`, `umi`, `cdna`, and `linker`.

The draft registry is in `docs/region_ontology_registry.yaml`.

The registry adds a controlled semantic layer. It lets tools distinguish a cell barcode, sample index, UMI, guide readout, and linker even when existing specs use overlapping free-text labels such as `barcode` or `named`.

## Core Idea

`sequence_type` describes what the interval is as a sequence.

- `fixed`: a known sequence is expected.
- `random`: any sequence of the expected length is allowed.
- `onlist`: the sequence should be present in a whitelist.
- `joined`: the region is composed of child regions.

`region_type` should describe what the interval does in the assay.

- partition reads by cell, molecule, nucleus, sample, or library.
- measure transcript, genome, guide, protein feature, or reporter signal.
- classify sample, feature, condition, or perturbation identity.
- provide a technical sequence needed for construction or sequencing.

This split matters because two regions can have the same `sequence_type` and different functions. A UMI and a cDNA insert may both be variable sequences, but the UMI partitions molecules while the cDNA insert measures transcript signal.

## Term Form

Ontology terms use a role-target pattern:

```text
RGN:<role>:<target>
```

Examples:

```text
RGN:partition:cell
RGN:partition:molecule
RGN:partition:sample
RGN:measure:transcript
RGN:measure:genome
RGN:classify:perturbation
RGN:technical:linker
```

A region may have multiple terms when it has multiple declared roles, including aggregate-level roles. During migration, `region_type` accepts either a legacy scalar label or a list of ontology terms. The `seqspec upgrade` command rewrites legacy labels into ontology-term lists.

Terms apply only to the region carrying them. A container term describes the
composite, not every child. Neither containment nor `related_terms` causes
automatic inheritance. For example, an ATAC molecule can contain both a genomic
insert and technical primers without making its primers genome measurements.

```yaml
region_type:
  - RGN:measure:guide
  - RGN:classify:perturbation
sequence_type: onlist
```

## Concrete Example

The main benefit is that one read interval can have more than one useful role. This is common in perturbation assays.

In `docs/examples/assays/sccrispra.spec.yaml`, the guide RNA region is currently labeled with one scalar value:

```yaml
region_id: gRNA
region_type: sgrna_target
name: Guide RNAs
sequence_type: onlist
```

After `seqspec upgrade`, the same region becomes:

```yaml
region_id: gRNA
region_type:
  - RGN:measure:guide
  - RGN:classify:perturbation
name: Guide RNAs
sequence_type: onlist
```

This is not just a rename. `RGN:measure:guide` says the read interval directly measures a guide sequence. `RGN:classify:perturbation` says that, after guide observations are aggregated with cell barcodes, the interval assigns perturbation identity.

These are different questions, and tools can now ask them directly:

```bash
seqspec find -m crispr -s region-type -i RGN:measure:guide sccrispra.0.5.yaml
seqspec find -m crispr -s region-type -i RGN:classify:perturbation sccrispra.0.5.yaml
```

Both commands return the `gRNA` region, but they do so for different reasons. The old label `sgrna_target` could not make that distinction machine-readable.

A sample index shows the same pattern:

```yaml
region_id: index7
region_type:
  - RGN:partition:sample
  - RGN:technical:index7
```

One tool can ask "which regions partition samples?" Another can ask "which region is the i7 technical index?" The same interval answers both queries without inventing a compound free-text label.

## Role Families

### Partition

A partition region contributes an identifier used to group reads or molecules.
Several regions may contribute jointly: a barcode tier need not identify a cell
by itself. Finite UMI collisions can occur even under perfect base measurement;
the term does not assert global uniqueness or high observed diversity.

```text
RGN:partition:cell
RGN:partition:nucleus
RGN:partition:molecule
RGN:partition:sample
RGN:partition:library
RGN:partition:feature
RGN:partition:perturbation
```

Examples: cell barcodes partition reads by cell, UMIs partition reads by original molecule, and i7/i5 indexes partition reads by sample or library.

### Measure

A measurement region carries the direct biological or molecular signal.

```text
RGN:measure:transcript
RGN:measure:genome
RGN:measure:chromatin_accessibility
RGN:measure:guide
RGN:measure:protein_feature
RGN:measure:reporter
```

Examples: cDNA measures transcript signal, genomic DNA measures genome-derived signal, and guide readout measures guide sequence.

### Classify

A classifier region maps an observed sequence value to a semantic class when observations of that read interval are aggregated.

```text
RGN:classify:sample
RGN:classify:feature
RGN:classify:perturbation
RGN:classify:condition
```

Examples: a guide sequence classifies perturbation identity after guide observations are aggregated with cell barcode observations. A hashtag, CMO, or MULTI-seq barcode classifies sample or multiplexed condition after observations of that tag are aggregated.

Classifier terms should describe direct assay intent, not arbitrary downstream analysis. cDNA measurements can later classify cell type, but the cDNA region itself should remain `RGN:measure:transcript`.

The distinction is scope. `partition`, `measure`, and `technical` terms annotate the nominal read interval directly. `classify` terms annotate semantic identity assigned when observations of that interval are used in aggregate.

This describes the claim, not merely whether a computation groups reads.
Counting transcript reads does not make a transcript region a classifier.
Likewise, looking up a feature barcode is not aggregate feature classification.
For example, an assay designed to assign antigen-binding specificity to a cell
from aggregated barcoded-antigen observations can declare `RGN:classify:feature`.
Guide observations can support an intended perturbation assignment but do not
prove that editing occurred or had an effect.

### Technical

A technical region is required for library construction, sequencing, capture, trimming, or validation.

```text
RGN:technical:adapter
RGN:technical:primer
RGN:technical:index
RGN:technical:linker
RGN:technical:spacer
RGN:technical:template_switch
RGN:technical:capture_sequence
RGN:technical:scaffold
```

A technical region can also have another role. An i7 index is both `RGN:partition:sample` and `RGN:technical:index`.

## Mapping Current Labels

Existing seqspec files use free-text region labels. Review these labels against
assay intent before treating their mapped terms as ground truth. Retain original
specs separately: upgrade replaces `region_type` and does not add a provenance field.

| ontology term | current labels and names |
|---|---|
| `RGN:partition:cell` | `barcode`, `cell_bc`, `cell_barcode`, `Cell Barcode`, `R2 Cell Barcode`, `10xbarcode`, `barcode-1`, `barcode-2`, `barcode-3`, `atac Cell Barcode 1`, `rna Cell Barcode 1` |
| `RGN:partition:nucleus` | same labels as cell barcodes, inferred from single-nucleus assay context |
| `RGN:partition:molecule` | `umi`, `UMI`, `GEX UMI`, `Protein UMI`, `crispr-umi`, `rna-umi`, `umi_rna`, `8-bp UMI` |
| `RGN:partition:sample` | `index5`, `index7`, `i5 index`, `i7 index`, `sample_index`, `HTO_bc`, `CMO Barcode`, `MULTI-seq barcode` |
| `RGN:partition:feature` | feature barcode regions, antibody barcode regions, some `HTO_bc` or `CMO Barcode` contexts |
| `RGN:partition:perturbation` | `sgrna_target`, `guide_target`, `crispr-guide_target`, `crispr_barcode`, `guide`, `guide sequence` |
| `RGN:measure:transcript` | `cdna`, `cDNA`, `RNA-cDNA`, `Read 1 cDNA sequence`, `RNA Read 1 sequence` |
| `RGN:measure:genome` | `gdna`, `gDNA`, `Genomic DNA`, `ATAC genomic DNA` |
| `RGN:measure:chromatin_accessibility` | `gdna` in ATAC or multiome context |
| `RGN:measure:guide` | `sgrna_target`, `guide_target`, `crispr-guide_target`, `guide`, `guide sequence`, `crispr_read2` |
| `RGN:measure:protein_feature` | `protein`, `protein-cDNA`, antibody or feature barcode regions |
| `RGN:measure:reporter` | `reporter_3prime_utr`, reporter oligo regions, MPRA-related inserts |
| `RGN:classify:perturbation` | `sgrna_target`, `guide_target`, `crispr-guide_target`, `guide sequence`, `crispr_barcode` |
| `RGN:classify:sample` | `HTO_bc`, `CMO Barcode`, `MULTI-seq barcode`, `sample_index`, `index5`, `index7` |
| `RGN:classify:feature` | `protein`, `protein-cDNA`, feature barcode regions, antibody barcode regions |
| `RGN:classify:condition` | `CMO Barcode`, `MULTI-seq barcode`, `HTO_bc` when these encode multiplexed conditions |
| `RGN:technical:adapter` | `illumina_p5`, `illumina_p7`, `Illumina P5`, `Illumina P7`, `p5`, `p7`, `ME`, `ME1`, `ME2` |
| `RGN:technical:primer` | `truseq_read1`, `truseq_read2`, `truseq_r1`, `truseq_r2`, `nextera_read1`, `nextera_read2`, `read1_primer`, `custom_primer`, `U6 primer` |
| `RGN:technical:index` | `index5`, `index7`, `i5 index`, `i7 index`, `sample_index`, `Index 1 (i7 index)`, `Index 2 (i5 index)` |
| `RGN:technical:linker` | `linker`, `linker1`, `linker2`, `linker3`, `linker-1`, `linker-2`, `atac linker`, `MULTI-seq linker`, `N10_linker`, `N9_linker` |
| `RGN:technical:spacer` | `spacer`, `spacer1`, `spacer2`, `spacer3`, `spacer4`, `double_T`, `triple_G` |
| `RGN:technical:template_switch` | `tso`, `TSO`, `bead_TSO`, `10x5pTSO` |
| `RGN:technical:capture_sequence` | `poly_T`, `polyT`, `ploy_T`, `poly_A`, `polyA`, `capture_sequence` |
| `RGN:technical:scaffold` | `sgrna_scaffold`, `guidebackbone`, `cs1_scaffold`, `CS1` |

## Ambiguous Labels

Some labels need context before they can be mapped safely.

| label | ambiguity |
|---|---|
| `barcode` | can mean cell, nucleus, sample, feature, guide, or generic partition barcode |
| `named` | placeholder term; does not state function |
| `dna` | can mean technical oligo, reporter, genomic insert, or scaffold |
| `crispr` | can mean guide sequence, perturbation classifier, or modality |
| `protein` | can mean protein feature signal or modality |
| `Cell Barcode` in single-nucleus assays | should likely map to `RGN:partition:nucleus` based on assay context |

Use `RGN:unknown:unclassified` when the evidence is not strong enough to assign a precise term. This is preferable to forcing a false mapping.

## Migration Path

Upgrade `region_type` from a legacy scalar label to a list of ontology terms.

```yaml
region_type:
  - RGN:partition:cell
sequence_type: onlist
```

Unmapped legacy labels upgrade to `RGN:unknown:unclassified`. The compatibility
table still maps some ambiguous labels to specific roles: `barcode` to cell,
`tag` to reporter, and indices to sample partitions. These historical defaults
are not verified assay annotations. Review them explicitly; names and aliases
do not trigger additional automatic mappings.

```yaml
region_type:
  - RGN:unknown:unclassified
```

This keeps seqspec backward compatible because old scalar labels still load, validate, and map to ontology terms at runtime.

Each registry term should define what it means, what it does not mean, typical `sequence_type` values, aliases, and concrete examples. These fields keep the ontology precise while allowing new terms to be added in versioned registry updates.

## Tool Use

`seqspec check` validates the nominal spec, not observed reads. It rejects
malformed ontology IDs and combining `RGN:unknown:unclassified` with another
term. It warns about unrecognized well-formed terms, which may be new terms or
typos, and explicit unclassified roles. Warnings do not cause a failing exit
status. Registry version 0.1.1-draft is bundled with the tool. No new spec fields
are required. Typical sequence types are guidance, not mandatory constraints;
`random` does not assert uniform sampling or high entropy.

seqcheck compares observed reads with declared sequence constraints. Neither a
term nor a typical sequence type by itself defines an empirical QC threshold.

Exact ontology queries test membership without inference. Compound legacy
queries require all mapped roles, except `index5` and `index7`, which select
their technical positions irrespective of sample/library assignment. Extraction
formats use the cellular barcode slot for cell or nucleus barcodes, while
ontology queries keep those identities distinct.

`seqspec diff` can use ontology terms to distinguish label drift from semantic changes. A change from `cell_bc` to `Cell Barcode` is minor if both map to `RGN:partition:cell`. A change from `RGN:partition:cell` to `RGN:partition:sample` is major.

Language-model tools can use ontology terms to parse seqspec files without relying on fragile free-text labels.

## Compatibility With Protocol Operations

Seqspec describes the final nominal library molecule. A protocol-operation model describes how that molecule is built. These are related but separate layers.

The operation layer uses rewrite rules such as `anneal`, `denature`, `ligate`, `cut`, `extend`, and `modify_end`. Those operations explain provenance: how regions are created, joined, copied, trimmed, or paired during library preparation.

The region ontology should describe the role of each region in the final molecule. It should not encode every operation that produced the region. For example, a template-switch oligo may arise through `anneal` and `extend`, but its final region role can still be `RGN:technical:template_switch`. A cDNA region may arise through reverse-transcription `extend`, but its final region role is `RGN:measure:transcript`.

This suggests a clean interface:

```yaml
region_id: rna-cdna
sequence_type: random
region_type:
  - RGN:measure:transcript
protocol_provenance:
  produced_by:
    - extend
```

The ontology answers what the final interval does. The protocol model answers how the interval came to exist. Keeping these layers separate lets seqspec remain a compact nominal description while still allowing future tools to verify that a machine-readable protocol can produce the declared library molecule.
