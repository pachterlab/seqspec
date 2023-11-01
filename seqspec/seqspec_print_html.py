from seqspec.Region import Region


def run_print_html(spec):
    # header = headerTemplate(spec.name, spec.doi, spec.description, spec.modalities)
    # header2 = "## Final Library"
    # assay_spec = multiModalTemplate(spec.assay_spec)
    # s = f"{header}\n{header2}\n{assay_spec}"
    s = htmlTemplate(spec)
    return s


def headerTemplate(name, doi, description, modalities):
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


def colorSeq(regions):
    return "".join(
        [f"<{r.region_type}>{r.sequence}</{r.region_type}>" for r in regions]
    )


def atomicRegionTemplate(
    region: Region,
    name,
    region_type,
    sequence_type,
    sequence,
    min_len,
    max_len,
    onlist,
    regions,
):
    seq = (
        colorSeq(region.get_leaves())
        if regions
        else f"<{region_type}>{sequence}</{region_type}>"
    )
    onlist = f"{onlist.filename} (md5: {onlist.md5})" if onlist else None
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

    # subseq = "<li>" + "</li><li>".join( [  for i in regions if regions else ''])
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
      <li>onlist: {onlist}</li>
      <li> regions: {subseq}
      </li>
  </details>
    """
    return s


def regionsTemplate(regions):
    s = f"""<ol><li>
    {'</li><li>'.join([atomicRegionTemplate(
                r,
                r.region_id,
                r.region_type,
                r.sequence_type,
                r.sequence,
                r.min_len,
                r.max_len,
                r.onlist,
                r.regions,
    ) for idx, r in enumerate(regions)])}
    </li></ol>"""
    return s


def libStructTemplate(region):
    s = f"""
  <h6 style="text-align: center">{region.name}</h6>
  <pre
    style="overflow-x: auto; text-align: left; background-color: #f6f8fa"
  >
{colorSeq(region.get_leaves())}</pre>
    """
    return s


def multiModalTemplate(assay_spec):
    s = "".join(
        [libStructTemplate(v) + "\n" + regionsTemplate(v.regions) for v in assay_spec]
    )
    return s


def htmlTemplate(spec):
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
        <div id="assay_spec">
          <h2>Final library</h2>
          {multiModalTemplate(spec.assay_spec)}
        </div>
      </div>
    </body>
  </html>
    """
    return s
