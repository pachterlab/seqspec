import os
from tempfile import TemporaryDirectory
from unittest import TestCase

from seqspec.Region import Onlist
from seqspec.seqspec_onlist import find_list_target_dir


class TestSeqspecOnlist(TestCase):
    def test_find_list_target_dir_local(self):
        with TemporaryDirectory(prefix="onlist_tmp_") as tmpdir:
            filename = os.path.join(tmpdir, "temp.txt")
            
            onlist1 = Onlist(filename, "d41d8cd98f00b204e9800998ecf8427e", "local")

            target_dir = find_list_target_dir([onlist1])
            self.assertEqual(target_dir, tmpdir)

    def test_find_list_target_dir_remote(self):
        onlist1 = Onlist("http:localhost:9/temp.txt", "d41d8cd98f00b204e9800998ecf8427e", "remote")

        target_dir = find_list_target_dir([onlist1])
        self.assertEqual(target_dir, os.getcwd())
        
