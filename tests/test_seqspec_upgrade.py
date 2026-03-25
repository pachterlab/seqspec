from pathlib import Path

from seqspec.seqspec_upgrade import seqspec_upgrade
from seqspec.utils import load_spec


def test_seqspec_upgrade_promotes_0_3_to_0_4():
    spec = load_spec(Path("tests/fixtures/legacy_0_3_scalar_protocols.yaml"), strict=False)
    assert spec.seqspec_version == "0.3.0"

    upgraded = seqspec_upgrade(spec, spec.seqspec_version)

    assert upgraded.seqspec_version == "0.4.0"


def test_seqspec_upgrade_promotes_0_2_to_0_4_and_adds_files():
    spec = load_spec(Path("tests/fixtures/legacy_0_2_missing_fields.yaml"), strict=False)
    assert spec.seqspec_version == "0.2.0"
    assert spec.sequence_spec[0].files == []

    upgraded = seqspec_upgrade(spec, spec.seqspec_version)

    assert upgraded.seqspec_version == "0.4.0"
    assert len(upgraded.sequence_spec[0].files) == 1
    assert upgraded.sequence_spec[0].files[0].file_id == upgraded.sequence_spec[0].read_id
