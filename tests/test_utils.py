from io import StringIO
import os
from unittest import TestCase

from seqspec.Region import Region
from seqspec.utils import load_spec_stream, get_cuts, write_read

from .test_region import (
    region_rna_joined_dict,
    region_rna_umi_dict,
    region_rna_linker_dict,
)

example_spec = """!Assay
seqspec_version: 0.0.0
assay: test_assay
name: my assay
doi: https://doi.org/10.1038/nmeth.1315
publication_date: 06 April 2009
description: first method to sequence the whole transcriptome (mRNA) of a single cell
sequencer: custom
modalities:
- rna
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/tang2009.html
assay_spec:
- !Region
  region_id: rna
  region_type: rna
  name: rna
  sequence_type: joined
  sequence: CCACTACGCCTCCGCTTTCCTCTCTATGGGCAGTCGGTGATXCGCCTTGGCCGTACAGCAGNNNNNNAGAGAATGAGGAACCCGGGGCAG
  min_len: 90
  max_len: 187
  onlist: null
  regions:
  - !Region
    region_id: SOLiD_P1_adapter
    region_type: custom_primer
    name: SOLiD_P1_adapter
    sequence_type: fixed
    sequence: CCACTACGCCTCCGCTTTCCTCTCTATGGGCAGTCGGTGAT
    min_len: 41
    max_len: 41
    onlist: null
    regions: null
    parent_id: rna
  - !Region
    region_id: cDNA
    region_type: cdna
    name: cDNA
    sequence_type: random
    sequence: X
    min_len: 1
    max_len: 98
    onlist: null
    regions: null
    parent_id: rna
  - !Region
    region_id: SOLiD_bc_adapter
    region_type: linker
    name: SOLiD_bc_adapter
    sequence_type: fixed
    sequence: CGCCTTGGCCGTACAGCAG
    min_len: 19
    max_len: 19
    onlist: null
    regions: null
    parent_id: rna
  - !Region
    region_id: index
    region_type: barcode
    name: index
    sequence_type: onlist
    sequence: NNNNNN
    min_len: 6
    max_len: 6
    onlist: !Onlist
      filename: index_onlist.txt
      md5: 939cb244b4c43248fcc795bbe79599b0
      location: local
    regions: null
    parent_id: rna
  - !Region
    region_id: p2_adapter
    region_type: custom_primer
    name: p2_adapter
    sequence_type: fixed
    sequence: AGAGAATGAGGAACCCGGGGCAG
    min_len: 23
    max_len: 23
    onlist: null
    regions: null
    parent_id: rna
"""


class TestUtils(TestCase):
    def test_load_spec_stream(self):
        with StringIO(example_spec) as instream:
            spec = load_spec_stream(instream)
        self.assertEqual(spec.name, "my assay")
        head = spec.get_modality("rna")
        self.assertEqual(len(head.regions), 5)

    def test_get_cuts(self):
        r_umi_dict = region_rna_umi_dict("region-2")
        r_umi = Region(**r_umi_dict)
        r_linker_dict = region_rna_linker_dict("region-3")
        r_linker = Region(**r_linker_dict)
        r_expected_dict = region_rna_joined_dict("region-1", [r_umi, r_linker])
        r_expected_dict["sequence"] = r_umi_dict["sequence"] + r_linker_dict["sequence"]
        r_expected = Region(**r_expected_dict)

        r_umi_min, r_umi_max = r_umi.get_len()
        r_linker_min, r_linker_max = r_linker.get_len()
        r_linker_min += r_umi_max
        r_linker_max += r_linker_max
        cuts = get_cuts(r_expected.regions)
        self.assertEqual(cuts, [(r_umi_min, r_umi_max), (r_linker_min, r_linker_max)])

    def test_write_header(self):
        stream = StringIO()
        header = "@string"
        sequence = "CANNTG"
        quality = "IIIIII"
        write_read(header, sequence, quality, stream)

        text = stream.getvalue().split(os.linesep)
        self.assertEqual(text[0], f"{header}")
        self.assertEqual(text[1], sequence)
        self.assertEqual(text[2], "+")
        self.assertEqual(text[3], quality)
