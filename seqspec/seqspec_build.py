"""Init module for seqspec CLI.

This module provides functionality to generate new seqspec files from a newick tree format.
"""

import asyncio
import logging
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path

from agents import Agent, ModelSettings, Runner, function_tool
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

from seqspec.Assay import Assay
from seqspec.utils import (
    JsonlSpanExporter,
    SummarySpanExporter,
    write_pydantic_to_file_or_stdout,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_build_args(parser) -> ArgumentParser:
    """Create and configure the build command subparser (simple draft creator)."""
    subparser = parser.add_parser(
        "build",
        description="""
Generate a complete seqspec with natural language.

Example:
seqspec build -o spec.yaml --description "An extensive description of the assay and sequencing reads" -n "seqspec generated with LLM" -m rna
""",
        help="Generate a complete seqspec with natural language.",
        formatter_class=RawTextHelpFormatter,
    )
    req = subparser.add_argument_group("required arguments")
    req.add_argument("-n", "--name", required=True, help="Assay name")
    req.add_argument(
        "-m",
        "--modalities",
        required=True,
        help="Comma-separated list of modalities (e.g. rna,atac)",
    )
    subparser.add_argument("--doi", default="", help="DOI of the assay")
    subparser.add_argument("--description", default="", help="Short description")
    subparser.add_argument("--date", default="", help="Date (YYYY-MM-DD)")
    subparser.add_argument(
        "--trace",
        type=Path,
        metavar="TRACE_JSONL",
        help="Write OpenTelemetry spans to this JSONL file for later viewing",
    )
    subparser.add_argument(
        "--verbose",
        nargs="?",
        const="simple",
        choices=["simple", "extended", "all"],
        help="Enable console tracing. Default mode is 'simple' if no value is given. "
        "Modes: simple | extended | all",
        default="simple",
    )
    subparser.add_argument(
        "-o", "--output", type=Path, metavar="OUT", help="Output YAML (default stdout)"
    )
    return subparser


def validate_build_args(
    _: ArgumentParser, args: Namespace
) -> None:  # simple draft needs no extra checks
    if not args.name:
        raise ValueError("Assay name is required")
    if not args.modalities:
        raise ValueError("Modalities must be provided")


def run_build(parser: ArgumentParser, args: Namespace) -> None:
    """Run the simplified build command."""
    validate_build_args(parser, args)

    modalities = [m.strip() for m in args.modalities.split(",") if m.strip()]
    spec = seqspec_build(
        args.name,
        args.doi,
        args.date,
        args.description,
        modalities,
        trace_path=args.trace,
        verbose_mode=args.verbose,
    )
    # Build empty assay with meta Regions only

    write_pydantic_to_file_or_stdout(spec, args.output)


async def seqspec_build_async(
    name,
    doi,
    date,
    description,
    modalities,
    trace_path: Path | None = None,
    verbose_mode: str | None = None,
) -> Assay:
    # minimal logger setup for exporters
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(h)
    logger.propagate = False
    logger.info(
        "NOTE: LLM tool calling is slow (~minutes) and imperfect. Manually check the resulting spec."
    )

    tracer_provider = trace_sdk.TracerProvider()

    # Console trace modes (exporters only)
    if verbose_mode == "all":
        tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    elif verbose_mode in {"simple", "extended"}:
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(SummarySpanExporter(logger, verbose_mode))
        )

    # Optional file trace
    if trace_path is not None:
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(JsonlSpanExporter(trace_path))
        )

    OpenAIAgentsInstrumentor().instrument(tracer_provider=tracer_provider)

    # tools import + decoration (unchanged)
    from seqspec.seqspec_check import seqspec_check
    from seqspec.seqspec_format import seqspec_format
    from seqspec.seqspec_init import seqspec_init
    from seqspec.seqspec_insert import seqspec_insert_reads, seqspec_insert_regions
    from seqspec.seqspec_modify import (
        seqspec_modify,
        seqspec_modify_read,
        seqspec_modify_region,
    )

    seqspec_check = function_tool(seqspec_check, strict_mode=False)
    seqspec_insert_reads = function_tool(seqspec_insert_reads, strict_mode=False)
    seqspec_insert_regions = function_tool(seqspec_insert_regions, strict_mode=False)
    seqspec_modify = function_tool(seqspec_modify, strict_mode=False)
    seqspec_modify_region = function_tool(seqspec_modify_region, strict_mode=False)
    seqspec_modify_read = function_tool(seqspec_modify_read, strict_mode=False)
    seqspec_format = function_tool(seqspec_format, strict_mode=False)

    AGENT_INSTRUCTIONS = """
Use the given tools to build a correct and complete seqspec file.
Do not hallucinate any data that is not provided.
The list of the top-most regions in the library_spec have region_ids that correspond to the "modality".
Add the sequencing library structure with seqspec_insert_region.
After, add the sequencing reads with seqspec_insert_read.
Check the file with seqspec_check.
Modify attributes of any elements with seqspec_modify if necessary.
At the very end, run seqspec_format then return the final spec.
"""

    spec: Assay = seqspec_init(name, doi, date, "description", modalities)
    logger.info("Created empty seqspec file.")
    logger.info("Initializing LLM Agent...")
    PROMPT = f"""
Name: {name}
DOI: {doi}
Date: {date}
Description: {description}
Modalities: {", ".join(modalities)}

spec

{spec.model_dump_json()}
"""

    agent = Agent(
        name="seqspec agent",
        instructions=AGENT_INSTRUCTIONS,
        model="o4-mini",
        tools=[
            seqspec_check,
            seqspec_insert_reads,
            seqspec_insert_regions,
            seqspec_modify_read,
            seqspec_modify_region,
            seqspec_format,
        ],
        output_type=Assay,
        model_settings=ModelSettings(temperature=1, tool_choice="auto"),
    )

    # Start the run
    streamed = Runner.run_streamed(agent, input=PROMPT)

    # Drain the stream quietly (no manual logging here).
    async for _ in streamed.stream_events():
        pass

    # Flush exporters
    try:
        tracer_provider.shutdown()
    finally:
        pass

    return streamed.final_output


def seqspec_build(
    name,
    doi,
    date,
    description,
    modalities,
    trace_path: Path | None = None,
    verbose_mode: str | None = None,
) -> Assay:
    return asyncio.run(
        seqspec_build_async(
            name, doi, date, description, modalities, trace_path, verbose_mode
        )
    )
