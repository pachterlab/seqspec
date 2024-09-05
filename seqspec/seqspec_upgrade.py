from seqspec.utils import load_spec
from seqspec.File import File
from seqspec.Region import Onlist


def setup_upgrade_args(parser):
    subparser = parser.add_parser(
        "upgrade",
        description="upgrade seqspec file",
        # help="upgrade seqspec file",
    )
    # subparser_required = subparser.add_argument_group("required arguments")

    subparser.add_argument("yaml", help="Sequencing specification yaml file")
    subparser.add_argument(
        "-o",
        metavar="OUT",
        help=("Path to output file"),
        type=str,
        default=None,
    )
    return subparser


def validate_upgrade_args(parser, args):
    fn = args.yaml
    o = args.o

    run_upgrade(spec_fn=fn, o=o)


def run_upgrade(spec_fn, o):
    spec = load_spec(spec_fn)
    version = spec.seqspec_version
    upgrade(spec, version)
    if o:
        spec.to_YAML(o)
    else:
        print(spec.to_YAML())


def upgrade(spec, version):
    UPGRADE = {
        "0.0.0": upgrade_0_2_0_to_0_3_0,
        "0.1.0": upgrade_0_1_0_to_0_3_0,
        "0.1.1": upgrade_0_1_1_to_0_3_0,
        "0.2.0": upgrade_0_2_0_to_0_3_0,
        "0.3.0": upgrade_0_3_0_to_0_3_0,
    }

    u = UPGRADE[version](spec)
    return u


def upgrade_0_3_0_to_0_3_0(spec):
    return spec


def upgrade_0_2_0_to_0_3_0(spec):
    # for backwards compatibilty, for specs < v0.3.0 set the files to empty
    # of the specs < v0.3.0, set the onlist regions with missing properties
    # if version.parse(spec.seqspec_version) < version.parse("0.3.0"):

    for r in spec.sequence_spec:
        r.set_files(
            [
                File(
                    file_id=r.read_id,
                    filename=r.read_id,
                    filetype="",
                    filesize=0,
                    url="",
                    urltype="",
                    md5="",
                )
            ]
        )

    for r in spec.library_spec:
        for lf in r.get_leaves():
            if lf.onlist is not None:
                filename = lf.onlist.filename
                location = lf.onlist.location
                md5 = lf.onlist.md5
                lf.onlist = Onlist(
                    file_id=filename,
                    filename=filename,
                    filetype="",
                    filesize=0,
                    url="",
                    urltype="",
                    md5=md5,
                    location=location,
                )
    spec.seqspec_version = "0.3.0"
    return spec


def upgrade_0_1_1_to_0_3_0(spec):
    return upgrade_0_2_0_to_0_3_0(spec)


def upgrade_0_1_0_to_0_3_0(spec):
    return upgrade_0_2_0_to_0_3_0(spec)


def upgrade_0_0_0_to_0_3_0(spec):
    return upgrade_0_2_0_to_0_3_0(spec)
