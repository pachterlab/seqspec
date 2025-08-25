import gzip
import io
import json
import logging
import os
import re
from pathlib import Path
from typing import IO, Any, Dict, List, Optional, Tuple, Union

import requests
import yaml
from Bio import GenBank
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
)

# at top of file with other imports
from opentelemetry.trace import StatusCode
from pydantic import ValidationError

from seqspec.Assay import (
    Assay,
    AssayInput,
    LibKitInput,
    LibProtocolInput,
    SeqKitInput,
    SeqProtocolInput,
)
from seqspec.File import File, FileInput
from seqspec.Read import Read, ReadInput
from seqspec.Region import Onlist, Region, RegionInput

# --- Known tags to strip from the YAML ---
KNOWN_TAGS = [
    "!Assay",
    "!File",
    "!LibProtocol",
    "!LibKit",
    "!SeqProtocol",
    "!SeqKit",
    "!Read",
    "!Onlist",
    "!Region",
]

# Regex pattern to match known tags in all common positions
TAG_PATTERN = re.compile(
    r"""(?x)  # verbose mode
    (^|\s|:)      # start of line, whitespace, or mapping colon
    ("""
    + "|".join(re.escape(tag) for tag in KNOWN_TAGS)
    + r""")
    (?=\s|$|[:\[\]{},])  # followed by space, end of line, or YAML structure characters
    """
)


def strip_yaml_tags(yaml_str: str) -> str:
    """
    Removes known YAML tags from anywhere in the input YAML text.
    """
    return TAG_PATTERN.sub(r"\1", yaml_str)


def safe_load_strip_tags(stream: Union[str, Path, IO]) -> dict:
    """
    Reads a YAML string or file-like object, strips known YAML tags,
    and safely loads it using yaml.safe_load().
    """
    if isinstance(stream, (str, Path)):
        with open(stream, "r") as f:
            raw = f.read()
    else:
        raw = stream.read()

    cleaned = strip_yaml_tags(raw)
    return yaml.safe_load(cleaned)


def format_pydantic_validation_object(error_path: str) -> str:
    """
    Converts a Pydantic validation error path to Python dictionary access notation.

    Args:
        error_path: Path like 'library_spec.0.regions.1.onlist.url'

    Returns:
        Python dictionary access notation like "spec['library_spec'][0]['regions'][1]['onlist']['url']"
    """
    if not error_path:
        return "spec"

    parts = error_path.split(".")
    result = "spec"

    for part in parts:
        # Check if part is a number (array index)
        if part.isdigit():
            result += f"[{part}]"
        else:
            result += f"['{part}']"

    return result


def load_spec(spec_fn: Union[str, Path], strict=True) -> Assay:
    """
    Loads a YAML or gzipped YAML spec file, strips tags, and constructs an Assay object.
    If strict=True and validation fails, prints all errors and raises an exception.
    """
    # Check if the file is gzip by reading the magic number
    with open(spec_fn, "rb") as f:
        magic = f.read(2)

    if magic == b"\x1f\x8b":
        with gzip.open(spec_fn, "rt") as stream:
            data_dict = safe_load_strip_tags(stream)
    else:
        with open(spec_fn, "r") as stream:
            data_dict = safe_load_strip_tags(stream)

    if strict:
        try:
            assay = Assay(**data_dict)
            # record the absolute path of the spec on the created object
            try:
                assay._spec_path = str(Path(spec_fn).resolve())
            except Exception:
                assay._spec_path = None
            return assay
        except ValidationError as e:
            verrors = e.errors()
            errors = []
            for idx, err in enumerate(verrors, 1):
                # err['loc'] is a tuple of the error path, join with dots for readability
                err_path = ".".join(str(x) for x in err.get("loc", []))
                err_type = err.get("type", "unknown")
                err_msg = err.get("msg", "")
                # Compose a descriptive error message
                errors.append(
                    {
                        "error_type": err_type,
                        "error_message": err_msg,
                        "error_object": format_pydantic_validation_object(err_path),
                        "full_error": err,
                    }
                )

            for idx, error in enumerate(errors, 1):
                print(
                    f"[error {idx}] {error['error_message']} in {error['error_object']}"
                )
            raise ValueError(
                "Invalid spec. Correct errors then verify spec with `seqspec format` and `seqspec check`."
            )
    else:
        from seqspec.Assay import AssayInput

        assay = AssayInput(**data_dict).to_assay()
        try:
            assay._spec_path = str(Path(spec_fn).resolve())
        except Exception:
            assay._spec_path = None
        return assay


def load_regions(
    regions_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[RegionInput]:
    """
    Load regions from a YAML/JSON file (optionally gzipped) or a file-like stream.

    The input is parsed into a list of RegionInput objects and converted to
    Region objects via RegionInput.to_region(). Supports two top-level formats:
    - A list of region dicts
    - A dict with key 'regions' that maps to the list
    """
    # Read YAML/JSON data or accept in-memory python objects
    if isinstance(regions_source, (dict, list)):
        data = regions_source
    elif isinstance(regions_source, (str, Path)):
        # If it's a Path-like or an existing file path, read from disk (with gzip auto-detect)
        if isinstance(regions_source, Path) or os.path.exists(str(regions_source)):
            # Detect gzip by magic bytes
            with open(regions_source, "rb") as f:  # type: ignore[arg-type]
                magic = f.read(2)

            if magic == b"\x1f\x8b":
                with gzip.open(regions_source, "rt") as stream:  # type: ignore[arg-type]
                    data = safe_load_strip_tags(stream)
            else:
                with open(regions_source, "r") as stream:  # type: ignore[arg-type]
                    data = safe_load_strip_tags(stream)
        else:
            # Treat as raw YAML/JSON content
            cleaned = strip_yaml_tags(str(regions_source))
            data = yaml.safe_load(cleaned)
    else:
        data = safe_load_strip_tags(regions_source)

    # Normalize to list of items
    if isinstance(data, dict):
        items = data.get("regions", [])
        # Allow single-region dicts as a convenience
        if items == [] and any(
            k in data for k in ("region_id", "region_type", "sequence_type")
        ):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    # Build Region objects from inputs
    region_inputs: List[RegionInput] = [
        it if isinstance(it, RegionInput) else RegionInput(**it) for it in items
    ]
    # regions: List[Region] = [ri.to_region() for ri in region_inputs]
    return region_inputs


def load_reads(
    reads_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[ReadInput]:
    """
    Load reads from a YAML/JSON file (optionally gzipped) or a file-like stream.

    The input is parsed into a list of ReadInput objects and converted to
    Read objects via ReadInput.to_read(). Supports two top-level formats:
    - A list of read dicts
    - A dict with key 'reads' that maps to the list
    """
    # Read YAML/JSON data or accept in-memory python objects
    if isinstance(reads_source, (dict, list)):
        data = reads_source
    elif isinstance(reads_source, (str, Path)):
        # If it's a Path-like or an existing file path, read from disk (with gzip auto-detect)
        if isinstance(reads_source, Path) or os.path.exists(str(reads_source)):
            # Detect gzip by magic bytes
            with open(reads_source, "rb") as f:  # type: ignore[arg-type]
                magic = f.read(2)

            if magic == b"\x1f\x8b":
                with gzip.open(reads_source, "rt") as stream:  # type: ignore[arg-type]
                    data = safe_load_strip_tags(stream)
            else:
                with open(reads_source, "r") as stream:  # type: ignore[arg-type]
                    data = safe_load_strip_tags(stream)
        else:
            # Treat as raw YAML/JSON content
            cleaned = strip_yaml_tags(str(reads_source))
            data = yaml.safe_load(cleaned)
    else:
        data = safe_load_strip_tags(reads_source)

    # Normalize to list of items
    if isinstance(data, dict):
        items = data.get("reads", [])
        # Allow single-read dicts as a convenience
        if items == [] and any(k in data for k in ("read_id", "primer_id", "modality")):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    # Build Read objects from inputs
    read_inputs: List[ReadInput] = [
        it if isinstance(it, ReadInput) else ReadInput(**it) for it in items
    ]
    # reads: List[Read] = [ri.to_read() for ri in read_inputs]
    return read_inputs


def _load_generic_items(
    source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
):
    """
    Internal: read YAML/JSON from various inputs, returning a python object.
    Mirrors behavior used by load_reads/load_regions.
    """
    if isinstance(source, (dict, list)):
        return source
    elif isinstance(source, (str, Path)):
        if isinstance(source, Path) or os.path.exists(str(source)):
            with open(source, "rb") as f:  # type: ignore[arg-type]
                magic = f.read(2)
            if magic == b"\x1f\x8b":
                with gzip.open(source, "rt") as stream:  # type: ignore[arg-type]
                    return safe_load_strip_tags(stream)
            else:
                with open(source, "r") as stream:  # type: ignore[arg-type]
                    return safe_load_strip_tags(stream)
        else:
            cleaned = strip_yaml_tags(str(source))
            return yaml.safe_load(cleaned)
    else:
        return safe_load_strip_tags(source)


def load_files(
    files_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[FileInput]:
    """
    Load files and return a list of FileInput objects.

    Supports either a list of file dicts or a dict with key 'files'.
    Also accepts a single file dict (detected by presence of 'file_id' or 'filename').
    """
    data = _load_generic_items(files_source)

    if isinstance(data, dict):
        items = data.get("files", [])
        if items == [] and any(k in data for k in ("file_id", "filename")):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return [it if isinstance(it, FileInput) else FileInput(**it) for it in items]


def load_seqkits(
    kits_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[SeqKitInput]:
    """
    Load sequence kits and return a list of SeqKitInput objects.
    Accepts list or dict with key 'seqkits', or a single-kit dict.
    """
    data = _load_generic_items(kits_source)

    if isinstance(data, dict):
        items = data.get("seqkits", [])
        if items == [] and any(k in data for k in ("kit_id", "name")):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return [it if isinstance(it, SeqKitInput) else SeqKitInput(**it) for it in items]


def load_seqprotocols(
    protocols_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[SeqProtocolInput]:
    """
    Load sequence protocols and return a list of SeqProtocolInput objects.
    Accepts list or dict with key 'seqprotocols', or a single-protocol dict.
    """
    data = _load_generic_items(protocols_source)

    if isinstance(data, dict):
        items = data.get("seqprotocols", [])
        if items == [] and any(k in data for k in ("protocol_id", "name")):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return [
        it if isinstance(it, SeqProtocolInput) else SeqProtocolInput(**it)
        for it in items
    ]


def load_libkits(
    kits_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[LibKitInput]:
    """
    Load library kits and return a list of LibKitInput objects.
    Accepts list or dict with key 'libkits', or a single-kit dict.
    """
    data = _load_generic_items(kits_source)

    if isinstance(data, dict):
        items = data.get("libkits", [])
        if items == [] and any(k in data for k in ("kit_id", "name")):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return [it if isinstance(it, LibKitInput) else LibKitInput(**it) for it in items]


def load_libprotocols(
    protocols_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[LibProtocolInput]:
    """
    Load library protocols and return a list of LibProtocolInput objects.
    Accepts list or dict with key 'libprotocols', or a single-protocol dict.
    """
    data = _load_generic_items(protocols_source)

    if isinstance(data, dict):
        items = data.get("libprotocols", [])
        if items == [] and any(k in data for k in ("protocol_id", "name")):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return [
        it if isinstance(it, LibProtocolInput) else LibProtocolInput(**it)
        for it in items
    ]


def load_assays(
    assays_source: Union[str, Path, IO, Dict[str, Any], List[Dict[str, Any]]],
) -> List[AssayInput]:
    """
    Load assay data and return a list of AssayInput objects.
    Accepts list or dict with key 'assays', or a single-assay dict (detected by 'assay_id').
    """
    data = _load_generic_items(assays_source)

    if isinstance(data, dict):
        items = data.get("assays", [])
        if items == [] and any(k in data for k in ("assay_id", "name")):
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return [it if isinstance(it, AssayInput) else AssayInput(**it) for it in items]


def load_spec_stream(spec_stream: IO) -> Assay:
    """
    Parses a YAML stream, strips tags, and returns a validated Assay object.
    """
    data_dict = safe_load_strip_tags(spec_stream)
    from seqspec.Assay import AssayInput

    assay = AssayInput(**data_dict).to_assay()
    return assay


def yaml_safe_dump(obj):
    if isinstance(obj, list):
        return [o.model_dump() if hasattr(o, "model_dump") else o for o in obj]
    elif hasattr(obj, "model_dump"):
        return obj.model_dump()
    else:
        return obj


def load_genbank(gbk_fn: str):
    with open(gbk_fn, "r") as stream:
        return load_genbank_stream(stream)


def load_genbank_stream(gbk_stream: io.IOBase):
    data: GenBank = GenBank.read(gbk_stream)  # type: ignore
    return data


def write_read(header, seq, qual, f):
    f.write(f"{header}\n{seq}\n+\n{qual}\n")


def write_pydantic_to_file_or_stdout(
    resource: Union[
        Read, File, Region, Assay, List[Read], List[File], List[Region], Assay
    ],
    output: Optional[Path],
) -> None:
    """Write spec to file or stdout."""
    dump = yaml_safe_dump(resource)

    # Handle output
    if output:
        with open(output, "w") as f:
            yaml.dump(dump, f, sort_keys=False)
    else:
        print(yaml.dump(dump, sort_keys=False))


def yield_onlist_contents(stream):
    for line in stream:
        yield line.strip().split()[0]


def read_local_list(onlist: Onlist, base_path: str = "") -> List[str]:
    filename = os.path.join(base_path, onlist.filename)
    stream = open(filename, "rb")
    # do we need to decompress?
    if filename.endswith(".gz"):
        stream = gzip.GzipFile(fileobj=stream)

    # convert to text stream
    stream = io.TextIOWrapper(stream)

    results = []
    for i in yield_onlist_contents(stream):
        results.append(i)
    stream.close()
    return results


def read_remote_list(onlist: Onlist, base_path: str = "") -> List[str]:
    """Given an onlist object read the local or remote data"""
    filename = str(onlist.filename)
    if onlist.url:
        filename = str(onlist.url)

    stream = None
    try:
        # open stream
        auth = get_remote_auth_token()
        response = requests.get(filename, stream=True, auth=auth)
        response.raise_for_status()
        # Read into an in-memory bytes buffer to satisfy type expectations
        content_buffer = io.BytesIO(response.content)

        # do we need to decompress?
        if filename.endswith(".gz"):
            # Read decompressed bytes into a new BytesIO to present IO[bytes]
            with gzip.GzipFile(fileobj=content_buffer) as gz:
                decompressed = gz.read()
            binary_stream = io.BytesIO(decompressed)
        else:
            binary_stream = content_buffer

        # convert to text stream
        stream = io.TextIOWrapper(binary_stream)

        results = []
        for i in yield_onlist_contents(stream):
            # add the new line when writing to file
            results.append(i)
    finally:
        if stream is None:
            print("Warning: unable to open barcode file {}".format(filename))
        else:
            stream.close()

    return results


def get_remote_auth_token():
    """Look for authentication tokens for accessing remote resources"""
    username = os.environ.get("IGVF_API_KEY")
    password = os.environ.get("IGVF_SECRET_KEY")
    if not (username is None or password is None):
        auth = (username, password)
    else:
        auth = None

    return auth


def region_ids_in_spec(seqspec, modality, region_ids):
    # return True if all region_ids are in seqspec
    spec = seqspec.get_libspec(modality)
    found = []
    for region_id in region_ids:
        found += [r.region_id for r in spec.get_region_by_id(region_id)]
    return found


def file_exists(uri):
    try:
        if uri.startswith("https://api.data.igvf.org"):
            auth = get_remote_auth_token()
            if auth is None:
                print("Warning: IGVF_API_KEY and IGVF_SECRET_KEY not set")
            r = requests.head(uri, auth=auth)
            if r.status_code == 307:
                # igvf download link will redirect to a presigned amazon s3 url, HEAD request will not work.
                r = requests.get(r.headers["Location"], headers={"Range": "bytes=0-0"})
                return r.status_code == 206
            return r.status_code == 200
        r = requests.head(uri)
        if r.status_code == 302:
            return file_exists(r.headers["Location"])
        return r.status_code == 200
    except requests.ConnectionError:
        return False


REGION_TYPE_COLORS = {
    "barcode": "#2980B9",
    "cdna": "#8E44AD",
    "custom_primer": "#3CB371",
    "fastq": "#F1C40F",
    "gdna": "#E67E22",
    "illumina_p5": "#E17A47",
    "illumina_p7": "#E17A47",
    "index5": "#4AB19D",
    "index7": "#4AB19D",
    "linker": "#1ABC9C",
    "me1": "#E74C3C",
    "me2": "#E74C3C",
    "nextera_read1": "#FF8000",
    "nextera_read2": "#FF8000",
    "poly_a": "#FF0000",
    "poly_g": "#C0C0C0",
    "poly_t": "#7F8C8D",
    "poly_c": "#2C3E50",
    "s5": "#EF3D59",
    "s7": "#EF3D59",
    "truseq_read1": "#EFC958",
    "truseq_read2": "#EFC958",
    "umi": "#16A085",
    "tag": "#344E5C",
    "protein": "#ECF0F1",
    "named": "#FF8C00",
}

# unused

# '#95A5A6'


def map_read_id_to_regions(
    spec: Assay, modality: str, read_id: str
) -> Tuple[Read, List[Region]]:
    # get the read object and primer id
    read = spec.get_read(read_id)
    primer_id = read.primer_id

    # get all atomic elements from library
    libspec = spec.get_libspec(modality)

    # get the (ordered) leaves ensuring region with primer_id is included (but not its children)
    leaves = libspec.get_leaves_with_region_id(primer_id)
    # print(leaves)
    # get the index of the primer in the list of leaves (ASSUMPTION, 5'->3' and primer can be any node)
    pidxs = [idx for idx, leaf in enumerate(leaves) if leaf.region_id == primer_id]
    if len(pidxs) == 0:
        raise IndexError(
            "primer_id {} not found in regions {}".format(
                primer_id, [leaf.region_id for leaf in leaves]
            )
        )
    primer_idx = pidxs[0]

    # If we are on the opposite strand, we go in the opposite way
    if read.strand == "neg":
        rgns = leaves[:primer_idx][::-1]
    else:
        rgns = leaves[primer_idx + 1 :]

    return (read, rgns)


### LLM Utils


class SummarySpanExporter(SpanExporter):
    """
    Simple: 1 line per span with key info. No args/outputs.
    Extended: includes tool args + outputs (truncated).
    """

    def __init__(self, logger: logging.Logger, mode: str):
        assert mode in {"simple", "extended"}
        self.logger = logger
        self.mode = mode

    def export(self, spans):
        for s in spans:
            attrs = dict(getattr(s, "attributes", {}) or {})

            # --- infer kind (LLM/TOOL/AGENT/...) ---
            # Primary: OpenInference attribute when OTLP transport is used
            kind = attrs.get("openinference.span.kind")
            # Fallbacks for robustness
            if not kind:
                # Some exporters encode kind directly or via presence of attrs
                if attrs.get("openinference.tool.name"):
                    kind = "TOOL"
                elif attrs.get("openinference.model") or attrs.get("llm.model_name"):
                    kind = "LLM"
                elif s.name.lower().startswith("agent"):
                    kind = "AGENT"
                else:
                    kind = "CHAIN"

            # --- outcome from span status ---
            status = getattr(getattr(s, "status", None), "status_code", None)
            if status == StatusCode.OK:
                result = "ok"
            elif status == StatusCode.ERROR:
                result = "error"
            else:
                result = "unset"

            # Optional extras
            tool_name = attrs.get("openinference.tool.name")
            model = attrs.get("openinference.model") or attrs.get("llm.model_name")

            if self.mode == "simple":
                # Compact, user-centric line
                # e.g. "[span] seqspec_insert_regions type=TOOL result=ok tool=seqspec_insert_regions"
                parts = [
                    f"[span] {s.name}",
                    f"type={kind}",
                    f"result={result}",
                ]
                if tool_name:
                    parts.append(f"tool={tool_name}")
                elif model:
                    parts.append(f"model={model}")
                self.logger.info(" ".join(parts))
                continue  # next span

            # ----- extended mode (existing behavior) -----
            # keep existing extended fields & truncation
            ctx = s.get_span_context()
            dur_ms = (
                (s.end_time - s.start_time) / 1e6
                if (s.end_time and s.start_time)
                else 0.0
            )

            model = attrs.get("openinference.model", model)  # reuse model if set above
            usage_in = attrs.get("openinference.usage.input_tokens")
            usage_out = attrs.get("openinference.usage.output_tokens")
            usage_reason = attrs.get("openinference.usage.reasoning_tokens")

            base = (
                f"[span] name={s.name} "
                f"trace={ctx.trace_id:032x} span={ctx.span_id:016x} "
                f"dur={dur_ms:.1f}ms"
            )

            extras = []
            if model:
                extras.append(f"model={model}")
            if tool_name:
                extras.append(f"tool={tool_name}")
            if (
                usage_in is not None
                or usage_out is not None
                or usage_reason is not None
            ):
                extras.append(
                    f"tokens(in={usage_in},out={usage_out},reason={usage_reason})"
                )
            extras.append(f"type={kind}")
            extras.append(f"result={result}")

            line = base + (" " + " ".join(extras) if extras else "")

            if self.mode == "extended":
                targs = attrs.get("openinference.tool.args")
                tout = attrs.get("openinference.tool.output")
                if targs is not None:
                    line += " args=" + _truncate_for_console(targs, 400)
                if tout is not None:
                    line += " output=" + _truncate_for_console(tout, 400)

            self.logger.info(line)

        return SpanExportResult.SUCCESS


def _truncate_for_console(val, limit: int = 400) -> str:
    try:
        s = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
    except Exception:
        s = str(val)
    return s if len(s) <= limit else s[:limit] + "…"


class JsonlSpanExporter(SpanExporter):
    """Writes spans as JSON lines for later analysis."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._fh = self.path.open("a", encoding="utf-8")

    def shutdown(self):
        try:
            self._fh.close()
        except Exception:
            pass

    def export(self, spans):
        import json

        for s in spans:
            ctx = s.get_span_context()
            # parent: may be None; when present it's a SpanContext
            parent_span_id = None
            try:
                if s.parent:
                    parent_span_id = f"{s.parent.span_id:016x}"
            except Exception:
                parent_span_id = None

            # times can be 0 if the span didn't end cleanly
            start = getattr(s, "start_time", 0) or 0
            end = getattr(s, "end_time", 0) or 0
            dur_ms = (end - start) / 1e6 if end and start else 0.0

            # attributes/events/resource: coerce to JSON-safe
            attrs = _json_safe_dict(getattr(s, "attributes", {}) or {})
            events = []
            try:
                for e in getattr(s, "events", []) or []:
                    events.append(
                        {
                            "name": getattr(e, "name", None),
                            "attributes": _json_safe_dict(
                                getattr(e, "attributes", {}) or {}
                            ),
                        }
                    )
            except Exception:
                pass

            resource_attrs = {}
            try:
                resource_attrs = _json_safe_dict(
                    getattr(s, "resource", None).attributes
                )  # <-- FIX
            except Exception:
                resource_attrs = {}

            rec = {
                "trace_id": f"{ctx.trace_id:032x}",
                "span_id": f"{ctx.span_id:016x}",
                "parent_span_id": parent_span_id,
                "name": s.name,
                "start_time_unix_nano": start,
                "end_time_unix_nano": end,
                "duration_ms": dur_ms,
                "attributes": attrs,
                "events": events,
                "resource": resource_attrs,
            }
            self._fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self._fh.flush()
        return SpanExportResult.SUCCESS


def _json_safe(obj):
    # keep it compact + resilient
    import json
    from pathlib import Path as _Path

    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, _Path):
        return str(obj)
    try:
        return json.loads(json.dumps(obj))  # best-effort coercion
    except Exception:
        return str(obj)


def _json_safe_dict(d):
    try:
        return {str(k): _json_safe(v) for k, v in dict(d).items()}
    except Exception:
        # last resort
        return {}
