"""Print HTML module for seqspec.

This module provides functionality to generate HTML representations of seqspec files.
It is used by the print command with the 'seqspec-html' format option.
"""
from typing import List, Optional

from seqspec.Assay import Assay
from seqspec.Region import Region, Onlist, complement_sequence
from seqspec.Read import Read, File
from seqspec.seqspec_print_utils import libseq


def print_seqspec_html(spec: Assay) -> str:
    """Generate HTML representation of seqspec."""
    return htmlTemplate(spec)


def headerTemplate(name: str, doi: str, description: str, modalities: List[str]) -> str:
    s = f"""<h1 style="text-align: center">{name}</h1>
  <ul>
    <li>
      <a href="{doi}"
        >{doi}</a
      >
    </li>
    <li>
      {description}
    </li>
    <li>{", ".join(modalities)}</li>
  </ul>
    """
    return s


def colorSeq(regions: List[Region]) -> str:
    return "".join(
        [f"<{r.region_type}>{r.sequence}</{r.region_type}>" for r in regions]
    )


def atomicRegionTemplate(
    region: Region,
    name: str,
    region_type: str,
    sequence_type: str,
    sequence: str,
    min_len: int,
    max_len: int,
    onlist: Optional[Onlist],
    regions: Optional[List[Region]],
) -> str:
    seq = (
        colorSeq(region.get_leaves())
        if regions
        else f"<{region_type}>{sequence}</{region_type}>"
    )

    ol = f"{onlist.filename} (md5: {onlist.md5})" if onlist else None
    lst = []
    if regions:
        for idx, r in enumerate(regions):
            s = atomicRegionTemplate(
                r,
                r.region_id,
                r.region_type,
                r.sequence_type,
                r.sequence,
                r.min_len,
                r.max_len,
                r.onlist,
                r.regions,
            )
            lst.append(s)
        subseq = "</li><li>".join(lst)
        subseq = f"<ol><li>{subseq}</li></ol>"
    else:
        subseq = ""

    s = f"""<details>
    <summary>{name}</summary>
    <ul>
      <li>region_type: {region_type}</li>
      <li>sequence_type: {sequence_type}</li>
      <li>
        sequence:
        <pre
        style="
        overflow-x: auto;
        text-align: left;
        margin: 0;
        display: inline;
        "
        >
{seq}</pre
        >
      </li>
      <li>min_len: {min_len}</li>
      <li>max_len: {max_len}</li>
      <li>onlist: {ol}</li>
      <li> regions: {subseq}
      </li>
    </ul>
  </details>
    """
    return s


def regionsTemplate(regions: List[Region]) -> str:
    templates = [
        atomicRegionTemplate(
            r,
            r.region_id,
            r.region_type,
            r.sequence_type,
            r.sequence,
            r.min_len,
            r.max_len,
            r.onlist,
            r.regions,
        )
        for idx, r in enumerate(regions)
    ]
    s = f"""<ol><li>
    {'</li><li>'.join(templates)}
    </li></ol>"""
    return s


def libStructTemplate(spec: Assay, modality: str) -> str:
    libspec = spec.get_libspec(modality)
    seqspec = spec.get_seqspec(modality)  # noqa
    p, n = libseq(spec, modality)

    cseq = colorSeq(libspec.get_leaves())
    seq = "\n".join(
        [
            "\n".join(p),
            cseq,
            complement_sequence(libspec.sequence),
            "\n".join(n),
        ]
    )
    s = f"""
  <h6 style="text-align: center">{modality}</h6>
  <pre
    style="overflow-x: auto; text-align: left; background-color: #f6f8fa"
  >
{seq}</pre>
    """
    return s


def atomicReadTemplate(read: Read) -> str:
    files = "".join(atomicFileTemplate(f) for f in read.files) if read.files else ""

    s = f"""
      <details>
        <summary>{read.name}</summary>
        <ul>
          <li>read_id: {read.read_id}</li>
          <li>primer_id: {read.primer_id}</li>
          <li>min_len: {read.min_len}</li>
          <li>max_len: {read.max_len}</li>
          <li>strand: {read.strand}</li>
          <li>
            files:
            <ul>
              {files}
            </ul>
          </li>
        </ul>
      </details>
    """
    return s


def atomicFileTemplate(file: File) -> str:
    s = f"""
        <li>{file.filename} (md5: {file.md5})</li>
    """
    return s


def readsTemplate(reads: List[Read]) -> str:
    s = f"""<ol><li>
    {'</li><li>'.join([atomicReadTemplate(r) for r in reads])}
    </li></ol>"""
    return s


def multiModalTemplate(spec: Assay) -> str:
    modes = spec.modalities
    s = ""
    for m in modes:
        libspec = spec.get_libspec(m)
        seqspec = spec.get_seqspec(m)

        s += f"""
          {libStructTemplate(spec, m)}
          <h3>Sequence structure</h3>
          {readsTemplate(seqspec)}
          <h4>Library structure</h4>
          {regionsTemplate(libspec.get_leaves())}
        """
    return s


def htmlTemplate(spec: Assay) -> str:
    s = f"""
  <!DOCTYPE html>
  <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>
      highlight {{
      color: green;
      }}

      illumina_p5 {{color:#08519c;}}
      illumina_p7 {{color:#a50f15;}}
      nextera_read1 {{color:#bcbddc;}}
      nextera_read2 {{color:#9ebcda;}}
      truseq_read1 {{color:#4a1486;}}
      truseq_read2 {{color:#6a51a3;}}
      ME {{color:#969696;}}
      s5 {{color:#6baed6;}}
      s7 {{color:#fc9272;}}
      barcode {{color:#f768a1;}}
      umi {{color:#807dba;}}
      gDNA {{color:#f03b20;}}
    cDNA {{color:#7e331f;}}
      </style>
    </head>
    <body>
      <div style="width: 75%; margin: 0 auto">
        <h6><a href="../../index.html">Back</a></h6>
        <div id="assay">
          {headerTemplate(
            spec.name,
            spec.doi,
            spec.description,
            spec.modalities
          )}
        </div>
        <div id="library_spec">
          <h2>Final library</h2>
          {multiModalTemplate(spec)}
        </div>
      </div>
    </body>
  </html>
    """
    return s
