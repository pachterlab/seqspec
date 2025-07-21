from io import StringIO
from unittest import TestCase

from matplotlib.figure import Figure

from seqspec.seqspec_print import (
    print_library_ascii,
    print_seqspec_png,
)
from seqspec.utils import load_spec_stream

