const yaml = require("js-yaml");
const fs = require("fs");

let AssayYamlType = new yaml.Type("!Assay", { kind: "mapping" });
let RegionYamlType = new yaml.Type("!Region", { kind: "mapping" });
let JoinYamlType = new yaml.Type("!Join", { kind: "mapping" });

let SCHEMA = yaml.DEFAULT_SCHEMA.extend([
  AssayYamlType,
  RegionYamlType,
  JoinYamlType,
]);

// Get document, or throw exception on error
let data;
let assay = "10x-RNA-ATAC";
let yaml_fn = `examples/${assay}/spec.yaml`;
let html_fn = `assays/${assay}.html`;
try {
  data = yaml.load(fs.readFileSync(yaml_fn, "utf8"), { schema: SCHEMA });
} catch (e) {
  console.log(e);
}

function headerTemplate(name, doi, description, modalities) {
  return `
  <h1 style="text-align: center">${name}</h1>
  <ul>
    <li>
      <a href="${doi}"
        >${doi}</a
      >
    </li>
    <li>
      ${description}
    </li>
    <li>${modalities.join(", ")}</li>
  </ul>
    `;
}

function atomicRegionTemplate(
  name,
  sequence_type,
  sequence,
  min_len,
  max_len,
  onlist
) {
  return `
  <details>
    <summary>${name}</summary>
    <ul>
      <li>sequence_type: ${sequence_type}</li>
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
${sequence}</pre
        >
      </li>
      <li>min_len: ${min_len}</li>
      <li>max_len: ${max_len}</li>
      <li>onlist: ${onlist}</li>
    </ul>
  </details>`;
}

function regionsTemplate(regions) {
  return `
  <ol>
  <li>
    ${Object.keys(regions)
      .map(function (key, index) {
        return atomicRegionTemplate(
          regions[key].name,
          regions[key].sequence_type,
          regions[key].sequence,
          regions[key].min_len,
          regions[key].max_len,
          regions[key].onlist
        );
      })
      .join("</li><li>")}</li>
  </ol>
  `;
}

function libStructTemplate(region) {
  return `
  <h6 style="text-align: center">${region.name}</h6>
  <pre
    style="overflow-x: auto; text-align: left; background-color: #f6f8fa"
  >
${region.sequence}</pre>
  `;
}

// console.log(
//   // headerTemplate(data.name, data.doi, data.description, data.modalities),
//   // atomicRegionTemplate(
//   //   data.assay_spec.RNA.join.regions.illumina_p5.name,
//   //   data.assay_spec.RNA.join.regions.illumina_p5.sequence_type,
//   //   data.assay_spec.RNA.join.regions.illumina_p5.sequence,
//   //   data.assay_spec.RNA.join.regions.illumina_p5.min_len,
//   //   data.assay_spec.RNA.join.regions.illumina_p5.max_len,
//   //   data.assay_spec.RNA.join.regions.illumina_p5.onlist
//   // ),
//   regionsTemplate(data.assay_spec.RNA.join.regions)
// );

function multiModalTemplate(assay_spec) {
  return `
  ${Object.keys(assay_spec)
    .map(function (key, index) {
      return (
        libStructTemplate(assay_spec[key]) +
        regionsTemplate(assay_spec[key].join.regions)
      );
    })
    .join("")}
  `;
}

function htmlTemplate(data) {
  return `
  <!DOCTYPE html>
  <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <link rel="stylesheet" type="../text/css" href="styles.css" />
    </head>
    <body>
      <div style="width: 75%; margin: 0 auto">
        <h6><a href="../index.html">Back</a></h6>
        <div id="assay">
          ${headerTemplate(
            data.name,
            data.doi,
            data.description,
            data.modalities
          )}
        </div>
        <div id="assay_spec">
          <h2>Final library</h2>
          ${multiModalTemplate(data.assay_spec)}
        </div>
      </div>
    </body>
  </html>
  `;
}

fs.writeFileSync(html_fn, htmlTemplate(data));
