function generateAssay() {
  var formData = {
    seqspec_version: $("#seqspec_version").val(),
    assay: $("#assay").val(),
    sequencer: $("#sequencer").val(),
    name: $("#name").val(),
    doi: $("#doi").val(),
    publication_date: $("#publication_date").val(),
    description: $("#description").val(),
    modalities: $("#modalities").val().split(","),
    sequence_spec: null,
    library_spec: null,
  };

  var yamlStr = jsyaml.dump(formData, { lineWidth: -1 });
  // this strips the - !Assay from the yaml output
  $("#assayOutput").text(`!Assay\n${yamlStr}`);
}

function loadExampleAssays() {
  // load example assays
  var container = $(".load-assay-examples-container");
  files = ["illumina_truseq_dual.spec.yaml"];
  files.forEach(function (file) {
    var filePath = "assays/" + file;
    var button = $("<button>")
      .addClass("loadAssayBtn")
      .attr("data-file-path", filePath)
      .text(file.split(".")[0]); // Removes the file extension for the button text
    container.append(button);
  });

  $(".loadAssayBtn").click(function () {
    console.log($(this).data("file-path"));
    var filePath = $(this).data("file-path"); // Retrieve the file path from the button

    $.ajax({
      url: filePath, // Use the file path to load the file
      dataType: "text", // Expecting a YAML/text response
      success: function (data) {
        // Assuming 'data' contains the YAML file content
        data = data.replace(/!Assay/g, ""); // Remove the YAML tag
        data = data.replace(/- !Read/g, "-"); // Remove the YAML tag
        data = data.replace(/- !Region/g, "-"); // Remove the YAML tag
        data = data.replace(/!Onlist/g, ""); // Remove the YAML tag
        console.log(data);
        var fileContent = jsyaml.load(data); // Convert YAML string to JavaScript object
        console.log("loading");
        // Populate the form
        $("#assay").val(fileContent.assay);
        $("#seqspec_version").val(fileContent.seqspec_version);
        $("#sequencer").val(fileContent.sequencer);
        $("#name").val(fileContent.name);
        $("#doi").val(fileContent.doi);
        $("#publication_date").val(fileContent.publication_date);
        $("#description").val(fileContent.description);
        // split modalities into array
        $("#modalities").val(fileContent.modalities);

        // Automatically generate and display the YAML
        generateAssay(); // This calls the previously defined generateAssay function
      },
      error: function (xhr, status, error) {
        console.error("Error loading file:", status, error);
      },
    });
  });
}
