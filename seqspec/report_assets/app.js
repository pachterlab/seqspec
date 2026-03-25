(function () {
  const dataElement = document.getElementById("seqspec-view-data");
  const app = document.getElementById("app");
  const tip = document.getElementById("mol-tip");
  const data = JSON.parse(dataElement.textContent);
  const repositoryUrl =
    window.SEQSPEC_REPOSITORY || "https://github.com/pachterlab/seqspec";
  const toolVersion = window.SEQSPEC_TOOL_VERSION || data.seqspec_version || "";
  const selected = {};

  function esc(value) {
    if (value == null || value === "") {
      return "\u2014";
    }
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
  }

  function fmtValue(value) {
    if (value == null || value === "") {
      return "\u2014";
    }
    if (typeof value === "boolean") {
      return value ? "true" : "false";
    }
    if (typeof value === "number") {
      return Number.isInteger(value) ? value.toLocaleString() : value.toPrecision(4);
    }
    return esc(value);
  }

  function lengthLabel(minLen, maxLen) {
    if (minLen === maxLen) {
      return `${fmtValue(minLen)} bp`;
    }
    return `${fmtValue(minLen)}-${fmtValue(maxLen)} bp`;
  }

  function bpRangeLabel(start, end) {
    return `${fmtValue(start)}-${fmtValue(end)} bp`;
  }

  function kvList(rows) {
    return `<div class="kv-list">${rows
      .map(
        ([key, value, mono]) =>
          `<div class="kv-row"><div class="kv-key">${esc(
            key,
          )}</div><div class="kv-value${mono ? " mono" : ""}">${value}</div></div>`,
      )
      .join("")}</div>`;
  }

  function detailSection(title, body) {
    if (!body) {
      return "";
    }
    return `<section class="detail-section"><div class="detail-title">${esc(
      title,
    )}</div><div class="detail-content">${body}</div></section>`;
  }

  function detailTable(title, rows, columns) {
    if (!rows || !rows.length) {
      return "";
    }
    const keys =
      columns ||
      Array.from(
        rows.reduce((seen, row) => {
          Object.keys(row).forEach((key) => seen.add(key));
          return seen;
        }, new Set()),
      );
    return detailSection(
      title,
      `<div class="table-wrap"><table><thead><tr>${keys
        .map((key) => `<th>${esc(key)}</th>`)
        .join("")}</tr></thead><tbody>${rows
        .map(
          (row) =>
            `<tr>${keys.map((key) => `<td>${fmtValue(row[key])}</td>`).join("")}</tr>`,
        )
        .join("")}</tbody></table></div>`,
    );
  }

  function pathLabel(pathNames) {
    return (pathNames || []).join(" / ");
  }

  function regionTooltip(region) {
    let html = `<div class="tip-name">${esc(region.name)}</div>`;
    html += `<div>${esc(region.region_type)} \u00b7 ${esc(
      region.sequence_type,
    )} \u00b7 ${esc(lengthLabel(region.min_len, region.max_len))}</div>`;
    html += `<div class="tip-dim">${esc(bpRangeLabel(region.bp_start, region.bp_end))}</div>`;
    if (!region.is_leaf) {
      html += `<div class="tip-dim">${esc(region.child_region_ids.length)} child regions</div>`;
    }
    if (region.sequence) {
      const preview =
        region.sequence.length <= 40
          ? region.sequence
          : `${region.sequence.slice(0, 37)}\u2026`;
      html += `<div class="tip-dim">${esc(preview)}</div>`;
    }
    return html;
  }

  function readTooltip(read) {
    let html = `<div class="tip-name">${esc(read.label || read.read_id)}</div>`;
    html += `<div>${esc(read.read_id)} \u00b7 ${esc(read.strand)} \u00b7 ${esc(
      lengthLabel(read.min_len, read.max_len),
    )}</div>`;
    html += `<div class="tip-dim">${esc(bpRangeLabel(read.start, read.end))} anchored at ${esc(
      read.primer_id,
    )}</div>`;
    return html;
  }

  function seqTypeColor(sequenceType) {
    if (sequenceType === "onlist") {
      return "var(--reg-onlist)";
    }
    if (sequenceType === "random") {
      return "var(--reg-random)";
    }
    return "var(--reg-fixed)";
  }

  function seqTypeStroke(sequenceType) {
    if (sequenceType === "onlist") {
      return "var(--reg-onlist-stroke)";
    }
    if (sequenceType === "random") {
      return "var(--reg-random-stroke)";
    }
    return "var(--reg-fixed-stroke)";
  }

  function regionIsSelected(region, currentSelection) {
    if (!currentSelection || currentSelection.kind !== "region") {
      return false;
    }
    return (region.path_region_ids || []).includes(currentSelection.id);
  }

  function buildMolSvg(modality) {
    const leafRegions = modality.regions || [];
    const regionNodes = modality.region_nodes || [];
    const groupRegions = regionNodes.filter((region) => !region.is_leaf);
    const reads = modality.reads || [];
    const totalBp =
      modality.total_bp || leafRegions.reduce((sum, region) => sum + region.len, 0);
    const currentSelection = selected[modality.modality] || null;

    const pad = { left: 10, right: 10 };
    const molW = 860;
    const barY = 70;
    const barH = 22;
    const svgW = molW + pad.left + pad.right;
    const bpScale = molW / Math.max(totalBp, 1);
    const minPx = 18;
    const groupGap = 12;
    const groupHeight = 8;
    const groupLevels = groupRegions.length
      ? Math.max(...groupRegions.map((region) => region.depth)) + 1
      : 0;
    const groupTrackTop = barY - groupLevels * groupGap - 4;
    const rects = [];

    let rawWidths = leafRegions.map((region) => region.len * bpScale);
    let deficit = 0;
    rawWidths = rawWidths.map((px) => {
      if (px < minPx) {
        deficit += minPx - px;
        return minPx;
      }
      return px;
    });
    if (deficit > 0) {
      const shrinkTotal = rawWidths
        .filter((px) => px > minPx)
        .reduce((sum, px) => sum + px, 0);
      if (shrinkTotal > 0) {
        rawWidths = rawWidths.map((px) =>
          px > minPx ? px - deficit * (px / shrinkTotal) : px,
        );
      }
    }

    let currentX = pad.left;
    leafRegions.forEach((region, index) => {
      const width = rawWidths[index];
      rects.push({ ...region, x: currentX, w: width });
      currentX += width;
    });

    function bpToX(bp) {
      if (bp <= 0) {
        return pad.left;
      }
      for (const region of rects) {
        if (bp <= region.bp_end) {
          const fraction = region.len === 0 ? 0 : (bp - region.bp_start) / region.len;
          return region.x + fraction * region.w;
        }
      }
      const last = rects[rects.length - 1];
      return last ? last.x + last.w : pad.left;
    }

    let svg = "";
    svg += `<line x1="${pad.left}" y1="${barY - 1}" x2="${currentX}" y2="${barY - 1}" stroke="var(--border)" stroke-width="0.5"/>`;
    svg += `<line x1="${pad.left}" y1="${barY + barH + 1}" x2="${currentX}" y2="${barY + barH + 1}" stroke="var(--border)" stroke-width="0.5"/>`;

    groupRegions.forEach((region) => {
      const x = bpToX(region.bp_start);
      const width = Math.max(bpToX(region.bp_end) - x, 1);
      const y = groupTrackTop + region.depth * groupGap;
      const selectedClass = regionIsSelected(region, currentSelection) ? " selected" : "";
      svg += `<rect class="group-rect${selectedClass}" data-kind="region" data-modality="${esc(
        modality.modality,
      )}" data-id="${esc(region.region_id)}" x="${x}" y="${y}" width="${width}" height="${groupHeight}" rx="2" />`;
      if (width > 42) {
        svg += `<text class="group-label" x="${x + 3}" y="${y - 2}">${esc(region.name)}</text>`;
      }
    });

    rects.forEach((region) => {
      const selectedClass = regionIsSelected(region, currentSelection) ? " selected" : "";
      svg += `<rect class="region-rect${selectedClass}" data-kind="region" data-modality="${esc(
        modality.modality,
      )}" data-id="${esc(region.region_id)}" x="${region.x}" y="${barY}" width="${region.w}" height="${barH}" rx="2" fill="${seqTypeColor(
        region.sequence_type,
      )}" stroke="${seqTypeStroke(region.sequence_type)}" stroke-width="0.5"/>`;
    });

    const labelY = barY + barH + 10;
    rects.forEach((region) => {
      const centerX = region.x + region.w / 2;
      if (region.w > 14) {
        svg += `<text class="region-label" x="${centerX}" y="${labelY}" text-anchor="end" transform="rotate(-40 ${centerX} ${labelY})">${esc(
          region.name,
        )}</text>`;
      }
    });

    svg += `<text class="bp-label" x="${pad.left}" y="${barY - 3}" text-anchor="middle">0</text>`;
    rects.forEach((region) => {
      svg += `<text class="bp-label" x="${region.x + region.w}" y="${barY - 3}" text-anchor="middle">${region.bp_end}</text>`;
    });

    const readColors = ["#1e40af", "#059669", "#d97706", "#dc2626", "#7c3aed"];
    const posReads = reads.filter((read) => read.strand === "pos");
    const negReads = reads.filter((read) => read.strand === "neg");

    function drawRead(read, yBase, above, colorIndex) {
      const color = readColors[colorIndex % readColors.length];
      const x1 = bpToX(read.start);
      const x2 = bpToX(read.end);
      const arrowSize = 5;
      const selectedClass =
        currentSelection && currentSelection.kind === "read" && currentSelection.id === read.read_id
          ? " selected"
          : "";
      const groupAttrs = `class="read-group${selectedClass}" data-kind="read" data-modality="${esc(
        modality.modality,
      )}" data-id="${esc(read.read_id)}"`;

      if (above) {
        const y = yBase;
        svg += `<g ${groupAttrs}><line x1="${x1}" y1="${y}" x2="${Math.max(
          x1,
          x2 - arrowSize,
        )}" y2="${y}" stroke="${color}" class="read-line"/><polygon points="${x2},${y} ${
          x2 - arrowSize
        },${y - arrowSize} ${x2 - arrowSize},${y + arrowSize}" fill="${color}" stroke="${color}"/><line x1="${x1}" y1="${y}" x2="${x1}" y2="${barY}" stroke="${color}" stroke-width="1" stroke-dasharray="2,2" opacity="0.4"/><text class="read-label" x="${
          x1 + 3
        }" y="${y - 5}" fill="${color}">${esc(read.label || read.read_id)}</text></g>`;
      } else {
        const y = yBase;
        svg += `<g ${groupAttrs}><line x1="${x2}" y1="${y}" x2="${Math.min(
          x2,
          x1 + arrowSize,
        )}" y2="${y}" stroke="${color}" class="read-line"/><polygon points="${x1},${y} ${
          x1 + arrowSize
        },${y - arrowSize} ${x1 + arrowSize},${y + arrowSize}" fill="${color}" stroke="${color}"/><line x1="${x2}" y1="${y}" x2="${x2}" y2="${
          barY + barH
        }" stroke="${color}" stroke-width="1" stroke-dasharray="2,2" opacity="0.4"/><text class="read-label" x="${
          x2 - 3
        }" y="${y + 13}" text-anchor="end" fill="${color}">${esc(
          read.label || read.read_id,
        )}</text></g>`;
      }
    }

    let posY = groupTrackTop - 14;
    posReads.forEach((read, index) => {
      drawRead(read, posY, true, index);
      posY -= 22;
    });

    let negY = barY + barH + 48;
    negReads.forEach((read, index) => {
      drawRead(read, negY, false, posReads.length + index);
      negY += 22;
    });

    const svgH = Math.max(negY + 10, barY + barH + 50);
    return `<svg class="mol-svg" viewBox="0 0 ${svgW} ${svgH}" width="100%" xmlns="http://www.w3.org/2000/svg">${svg}</svg>`;
  }

  function selectorRow(config) {
    const {
      modalityName,
      kind,
      id,
      label,
      sub,
      meta,
      active,
      depth = 0,
      nodeType = "",
      hasChildren = false,
    } = config;
    const padding = kind === "region" ? 10 + depth * 16 : 10;
    const marker = kind === "region" ? (hasChildren ? "\u25a1" : "\u2022") : "\u2192";
    const typeClass = nodeType ? ` ${nodeType}` : "";

    return `<button class="selector-row${active ? " active" : ""}${typeClass}" data-kind="${esc(
      kind,
    )}" data-modality="${esc(modalityName)}" data-id="${esc(id)}"><span class="selector-main"><span class="selector-label-line" style="padding-left:${padding}px"><span class="selector-marker">${marker}</span><span class="selector-label">${esc(
      label,
    )}</span></span>${
      sub
        ? `<span class="selector-sub" style="padding-left:${padding + 16}px">${esc(sub)}</span>`
        : ""
    }</span><span class="selector-meta">${esc(meta)}</span></button>`;
  }

  function selectorHtml(modality) {
    const currentSelection = selected[modality.modality] || null;
    const regionRows = (modality.region_nodes || []).map((region) =>
      selectorRow({
        modalityName: modality.modality,
        kind: "region",
        id: region.region_id,
        label: region.name,
        sub: `${region.region_type} \u00b7 ${region.sequence_type}`,
        meta: region.is_leaf
          ? `${bpRangeLabel(region.bp_start, region.bp_end)}`
          : `${bpRangeLabel(region.bp_start, region.bp_end)} \u00b7 ${
              region.child_region_ids.length
            } children`,
        active:
          currentSelection &&
          currentSelection.kind === "region" &&
          currentSelection.id === region.region_id,
        depth: region.depth || 0,
        nodeType: region.is_leaf ? "leaf" : "branch",
        hasChildren: !region.is_leaf,
      }),
    );

    const readRows = (modality.reads || []).map((read) =>
      selectorRow({
        modalityName: modality.modality,
        kind: "read",
        id: read.read_id,
        label: read.label || read.read_id,
        sub: `${read.strand} \u00b7 ${read.primer_id}`,
        meta: bpRangeLabel(read.start, read.end),
        active:
          currentSelection && currentSelection.kind === "read" && currentSelection.id === read.read_id,
        depth: 0,
      }),
    );

    return `<div class="selector-pane"><div class="selector-group"><div class="selector-head">regions</div><div class="selector-body">${
      regionRows.join("") || '<div class="empty-state">No regions.</div>'
    }</div></div><div class="selector-group"><div class="selector-head">reads</div><div class="selector-body">${
      readRows.join("") || '<div class="empty-state">No reads.</div>'
    }</div></div></div>`;
  }

  function detailShell(header, sections) {
    return `<div class="detail-shell"><div class="detail-shell-head">${header}</div><div class="detail-shell-body">${sections.join(
      "",
    )}</div></div>`;
  }

  function modalitySummary(modality) {
    const rows = [
      ["modality", esc(modality.modality), true],
      ["library region", esc(modality.library_region_id), true],
      ["total length", esc(`${modality.total_bp} bp`), true],
      ["region count", esc(modality.region_nodes.length), true],
      ["read count", esc(modality.reads.length), true],
    ];

    const sections = [
      detailSection(
        "summary",
        `<div class="selection-note">Select a region or read to inspect its metadata.</div>${kvList(
          rows,
        )}`,
      ),
      detailTable("sequence protocols", modality.sequence_protocols, ["protocol_id", "name"]),
      detailTable("sequence kits", modality.sequence_kits, ["kit_id", "name"]),
      detailTable("library protocols", modality.library_protocols, ["protocol_id", "name"]),
      detailTable("library kits", modality.library_kits, ["kit_id", "name"]),
    ].filter(Boolean);

    return detailShell("modality", sections);
  }

  function regionDetails(modality, region) {
    const children = (modality.region_nodes || []).filter(
      (node) => node.parent_region_id === region.region_id,
    );
    const rows = [
      ["region id", esc(region.region_id), true],
      ["name", esc(region.name), false],
      ["path", esc(pathLabel(region.path_names)), true],
      ["region type", esc(region.region_type), true],
      ["sequence type", esc(region.sequence_type), true],
      ["length", esc(lengthLabel(region.min_len, region.max_len)), true],
      ["bp range", esc(bpRangeLabel(region.bp_start, region.bp_end)), true],
      ["leaf", esc(region.is_leaf ? "true" : "false"), true],
      ["children", esc(region.child_region_ids.length), true],
    ];

    const sections = [
      detailSection("metadata", kvList(rows)),
      region.sequence
        ? detailSection("sequence", `<pre class="region-seq">${esc(region.sequence)}</pre>`)
        : "",
      children.length
        ? detailTable(
            "child regions",
            children.map((child) => ({
              region_id: child.region_id,
              name: child.name,
              region_type: child.region_type,
              sequence_type: child.sequence_type,
              bp_range: bpRangeLabel(child.bp_start, child.bp_end),
              length: child.len,
            })),
            ["region_id", "name", "region_type", "sequence_type", "bp_range", "length"],
          )
        : "",
      region.onlist
        ? detailTable("onlist", [region.onlist], [
            "file_id",
            "filename",
            "filetype",
            "urltype",
            "url",
            "md5",
          ])
        : "",
    ].filter(Boolean);

    return detailShell(`region \u00b7 ${esc(region.name)}`, sections);
  }

  function readDetails(read) {
    const rows = [
      ["read id", esc(read.read_id), true],
      ["name", esc(read.name), false],
      ["strand", esc(read.strand), true],
      ["primer id", esc(read.primer_id), true],
      ["length", esc(lengthLabel(read.min_len, read.max_len)), true],
      ["bp range", esc(bpRangeLabel(read.start, read.end)), true],
    ];

    const sections = [
      detailSection("metadata", kvList(rows)),
      detailTable("files", read.files, ["file_id", "filename", "filetype", "urltype", "url", "md5"]),
    ].filter(Boolean);

    return detailShell(`read \u00b7 ${esc(read.label || read.read_id)}`, sections);
  }

  function selectionHtml(modality) {
    const currentSelection = selected[modality.modality] || null;
    if (!currentSelection) {
      return modalitySummary(modality);
    }
    if (currentSelection.kind === "region") {
      const region = (modality.region_nodes || []).find(
        (node) => node.region_id === currentSelection.id,
      );
      if (region) {
        return regionDetails(modality, region);
      }
    }
    if (currentSelection.kind === "read") {
      const read = (modality.reads || []).find((node) => node.read_id === currentSelection.id);
      if (read) {
        return readDetails(read);
      }
    }
    return modalitySummary(modality);
  }

  function assaySummary() {
    const rows = [
      ["assay id", esc(data.assay_id), true],
      ["name", esc(data.assay_name), false],
      ["seqspec version", esc(data.seqspec_version || toolVersion), true],
      ["date", esc(data.date || ""), false],
      [
        "doi",
        data.doi
          ? `<a class="inline-link" href="${esc(data.doi)}">${esc(data.doi)}</a>`
          : "\u2014",
        false,
      ],
      [
        "library structure",
        data.lib_struct
          ? `<a class="inline-link" href="${esc(data.lib_struct)}">${esc(data.lib_struct)}</a>`
          : "\u2014",
        false,
      ],
      [
        "modalities",
        esc((data.modalities || []).map((modality) => modality.modality).join(", ")),
        true,
      ],
    ];
    return `<div class="section"><div class="section-head">Assay</div><div class="section-body"><div class="description">${esc(
      data.description || "",
    )}</div>${kvList(rows)}</div></div>`;
  }

  function render() {
    const modalities = data.modalities || [];
    let html = `<div class="hdr"><div class="hdr-title">seqspec view</div><div class="hdr-row"><span class="l">assay</span> ${esc(
      data.assay_name,
    )}<span class="sep">|</span><span class="l">id</span> ${esc(
      data.assay_id,
    )}<span class="sep">|</span><span class="l">version</span> ${esc(
      data.seqspec_version || toolVersion,
    )}<span class="sep">|</span><span class="l">repo</span> <a class="inline-link" href="${esc(
      repositoryUrl,
    )}">${esc(repositoryUrl)}</a></div></div>`;
    html += assaySummary();

    modalities.forEach((modality) => {
      html += `<div class="modality-section"><div class="modality-head"><div class="modality-title">${esc(
        modality.modality,
      )}</div><div class="modality-meta">${esc(
        `${modality.region_nodes.length} regions · ${modality.reads.length} reads · ${modality.total_bp} bp`,
      )}</div></div><div class="mol-body">${buildMolSvg(
        modality,
      )}</div><div class="mol-legend"><span><span class="leg-swatch" style="background:var(--reg-fixed)"></span>fixed</span><span><span class="leg-swatch" style="background:var(--reg-onlist)"></span>onlist</span><span><span class="leg-swatch" style="background:var(--reg-random)"></span>random</span><span><span class="leg-swatch outline"></span>nested region span</span></div><div class="detail-layout">${selectorHtml(
        modality,
      )}<div class="detail-pane">${selectionHtml(modality)}</div></div></div>`;
    });

    app.innerHTML = html;
    bind();
  }

  function bind() {
    document.querySelectorAll("[data-kind][data-modality][data-id]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const modality = element.getAttribute("data-modality");
        const kind = element.getAttribute("data-kind");
        const id = element.getAttribute("data-id");
        const existing = selected[modality];
        if (existing && existing.kind === kind && existing.id === id) {
          delete selected[modality];
        } else {
          selected[modality] = { kind, id };
        }
        render();
      });
    });

    document.querySelectorAll(".region-rect[data-id], .group-rect[data-id]").forEach((element) => {
      const modality = element.getAttribute("data-modality");
      const regionId = element.getAttribute("data-id");
      const mod = (data.modalities || []).find((item) => item.modality === modality);
      const region = mod && (mod.region_nodes || []).find((item) => item.region_id === regionId);
      if (!region) {
        return;
      }
      element.addEventListener("mouseenter", () => {
        tip.innerHTML = regionTooltip(region);
        tip.classList.add("show");
      });
      element.addEventListener("mousemove", (event) => {
        tip.style.left = `${event.clientX + 12}px`;
        tip.style.top = `${event.clientY - 10}px`;
      });
      element.addEventListener("mouseleave", () => {
        tip.classList.remove("show");
      });
    });

    document.querySelectorAll(".read-group[data-id]").forEach((element) => {
      const modality = element.getAttribute("data-modality");
      const readId = element.getAttribute("data-id");
      const mod = (data.modalities || []).find((item) => item.modality === modality);
      const read = mod && (mod.reads || []).find((item) => item.read_id === readId);
      if (!read) {
        return;
      }
      element.addEventListener("mouseenter", () => {
        tip.innerHTML = readTooltip(read);
        tip.classList.add("show");
      });
      element.addEventListener("mousemove", (event) => {
        tip.style.left = `${event.clientX + 12}px`;
        tip.style.top = `${event.clientY - 10}px`;
      });
      element.addEventListener("mouseleave", () => {
        tip.classList.remove("show");
      });
    });
  }

  render();
})();
