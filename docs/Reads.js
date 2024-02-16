function generateRead() {
  var formData = {
    read_id: $("#read_id").val(),
    read_name: $("#read_name").val(),
    read_modality: $("#modality").val(),
    primer_id: $("#primer_id").val(),
    min_len: parseInt($("#read_min_len").val()),
    max_len: parseInt($("#read_max_len").val()),
    strand: $("#strand").val(),
  };

  var yamlStr = jsyaml.dump(formData, { lineWidth: -1 });
  // this strips the - !Region from the yaml output
  $("#readOutput").text(
    `- !Read\n${yamlStr
      .split("\n")
      .map((line) => "  " + line)
      .join("\n")}`
  );
}

function loadExampleReads() {
  var container = $(".load-read-examples-container");
  files = ["illumina_miseq.read.yaml"];
  files.forEach(function (file) {
    var filePath = "reads/" + file;
    var button = $("<button>")
      .addClass("loadReadBtn")
      .attr("data-file-path", filePath)
      .text(file.split(".")[0]); // Removes the file extension for the button text
    container.append(button);
  });

  $(".loadReadBtn").click(function () {
    console.log($(this).data("file-path"));
    var filePath = $(this).data("file-path"); // Retrieve the file path from the button

    $.ajax({
      url: filePath, // Use the file path to load the file
      dataType: "text", // Expecting a YAML/text response
      success: function (data) {
        // Assuming 'data' contains the YAML file content
        data = data.replace(/- !Read/g, ""); // Remove the YAML tag
        var fileContent = jsyaml.load(data); // Convert YAML string to JavaScript object

        // Populate the form
        $("#read_id").val(fileContent.read_id);
        $("#read_name").val(fileContent.read_name);
        $("#read_modality").val(fileContent.modality);
        $("#primer_id").val(fileContent.primer_id);
        $("#read_min_len").val(fileContent.min_len);
        $("#read_max_len").val(fileContent.max_len);
        $("#strand").val(fileContent.strand);

        // Automatically generate and display the YAML
        generateRead(); // This calls the previously defined generateRead function
      },
      error: function (xhr, status, error) {
        console.error("Error loading file:", status, error);
      },
    });
  });
}
