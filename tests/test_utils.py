import gzip
from hashlib import md5
from io import StringIO, BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from requests import HTTPError
from unittest import TestCase
from unittest.mock import patch

from seqspec.Region import (
    Region, RegionCoordinate, Onlist, project_regions_to_coordinates
)
from seqspec.utils import (
    get_remote_auth_token,
    load_spec_stream,
    map_read_id_to_regions,
    write_read,
    read_local_list,
    read_remote_list,
    yield_onlist_contents
)
from seqspec import __version__

from .test_region import (
    region_rna_joined_dict,
    region_rna_umi_dict,
    region_rna_linker_dict,
)

example_spec = f"""!Assay
seqspec_version: { __version__ }
assay_id: test_assay
name: my assay
doi: https://doi.org/10.1038/nmeth.1315
date: 06 April 2009
description: first method to sequence the whole transcriptome (mRNA) of a single cell
sequencer: custom
modalities:
- rna
lib_struct: https://teichlab.github.io/scg_lib_structs/methods_html/tang2009.html
library_protocol: custom 1
library_kit: custom 2
sequence_protocol: custom 3
sequence_kit: custom 4
sequence_spec:
- !Read
  read_id: read1.fastq.gz
  name: "Read1 for experiment"
  modality: rna
  primer_id: SOLiD_P1_adapter
  min_len: 90
  max_len: 187
  # this is a guess
  strand: pos
- !Read
  read_id: read2.fastq.gz
  name: read2 for experiment
  modality: rna
  primer_id: p2_adapter
  min_len: 25
  max_len: 25
  strand: neg
library_spec:
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
    sequence: XXXXXXXXXXXXXXXXXXXX
    min_len: 1
    max_len: 20
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

def load_example_spec(spec_text):
    with StringIO(spec_text) as instream:
        spec = load_spec_stream(instream)
    return spec


class TestUtils(TestCase):
    def test_load_spec_stream(self):
        spec = load_example_spec(example_spec)
        self.assertEqual(spec.name, "my assay")
        head = spec.get_libspec("rna")
        self.assertEqual(len(head.regions), 5)

    def test_project_regions_to_coordinates(self):
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

        umi_region = RegionCoordinate(r_umi, r_umi_min, r_umi_max)
        linker_region = RegionCoordinate(r_linker, r_linker_min, r_linker_max)

        cuts = project_regions_to_coordinates(r_expected.regions)
        self.assertEqual(cuts, [umi_region, linker_region])

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

    def test_yield_onlist_contents(self):
        fake_onlist = ["ATATATAT", "GCGCGCGC"]
        fake_stream = StringIO("{}\n".format("\n".join(fake_onlist)))

        response = list(yield_onlist_contents(fake_stream))
        self.assertEqual(response, fake_onlist)

    def test_read_local_list(self):
        fake_onlist = ["ATATATAT", "GCGCGCGC"]
        fake_contents = "{}\n".format("\n".join(fake_onlist))
        fake_md5 = md5(fake_contents.encode("ascii")).hexdigest()

        with TemporaryDirectory(prefix="onlist_tmp_") as tmpdir:
            temp_list_filename = os.path.join(tmpdir, "index.txt.gz")
            with gzip.open(temp_list_filename, "wt") as stream:
                stream.write(fake_contents)

            onlist1 = Onlist(temp_list_filename, fake_md5, "local")
            loaded_list = read_local_list(onlist1)

            self.assertEqual(fake_onlist, loaded_list)

    def test_read_local_list_gz(self):
        fake_onlist = ["ATATATAT", "GCGCGCGC"]
        fake_contents = "{}\n".format("\n".join(fake_onlist))
        fake_md5 = md5(fake_contents.encode("ascii")).hexdigest()

        with TemporaryDirectory(prefix="onlist_tmp_") as tmpdir:
            temp_list_filename = os.path.join(tmpdir, "index.txt")
            with open(temp_list_filename, "wt") as stream:
                stream.write(fake_contents)

            onlist1 = Onlist(temp_list_filename, fake_md5, "local")
            loaded_list = read_local_list(onlist1)

            self.assertEqual(fake_onlist, loaded_list)

    def test_read_remote_list(self):
        fake_onlist = ["ATATATAT", "GCGCGCGC"]
        fake_contents = "{}\n".format("\n".join(fake_onlist))
        fake_md5 = md5(fake_contents.encode("ascii")).hexdigest()

        def fake_request_get(url, stream=False, **kwargs):
            class response:
                def __init__(self):
                    self.raw = BytesIO(fake_contents.encode("utf-8"))
                    self.status_code = 200

                def raise_for_status(self):
                    if self.status_code != 200:
                        raise HTTPError(self.status_code)

            return response()

        with patch("requests.get", new=fake_request_get):
            onlist1 = Onlist("http://localhost/testlist.txt", fake_md5, "remote")
            loaded_list = read_remote_list(onlist1)

            self.assertEqual(fake_onlist, loaded_list)

    def test_get_igvf_auth(self):
        test_data = [
            (None, None, None),
            ("user", "pass", ("user", "pass")),
        ]

        igvf_variables = ["IGVF_API_KEY", "IGVF_SECRET_KEY"]
        previous = {name: os.environ.get(name) for name in igvf_variables}

        for username, password, expected in test_data:
            if username is not None:
                os.environ["IGVF_API_KEY"] = username
            if password is not None:
                os.environ["IGVF_SECRET_KEY"] = password

            auth = get_remote_auth_token()
            self.assertEqual(auth, expected)

        for name in igvf_variables:
            if previous[name] is None:
                del os.environ[name]
            else:
                os.environ[name] = previous[name]

    def test_map_read_id_to_regions(self):
        spec = load_example_spec(example_spec)

        read1_id = "read1.fastq.gz"
        read, region = map_read_id_to_regions(spec, "rna", read1_id)
        self.assertEqual(read.read_id, read1_id)
        self.assertEqual(len(region), 4)
        expected_regions = [
            (0, "cDNA"),
            (1, "SOLiD_bc_adapter"),
            (2, "index"),
            (3, "p2_adapter"),
        ]
        for i, region_id in expected_regions:
            self.assertEqual(region[i].region_id, region_id)
        self.assertRaises(IndexError, map_read_id_to_regions, spec, "rna", "foo")
