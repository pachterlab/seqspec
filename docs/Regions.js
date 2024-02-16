function generateRegion() {
  var formData = {
    region_id: $("#region_id").val(),
    region_type: $("#region_type").val(),
    name: $("#name").val(),
    sequence_type: $("#sequence_type").val(),
    sequence: $("#sequence").val(),
    min_len: parseInt($("#min_len").val()),
    max_len: parseInt($("#max_len").val()),
    onlist: $("#onlist_location").val()
      ? {
          location: $("#onlist_location").val(),
          filename: $("#onlist_filename").val(),
          md5: $("#onlist_md5").val(),
        }
      : null,
    regions: null,
  };

  var yamlStr = jsyaml.dump(formData, { lineWidth: -1 });
  // this strips the - !Region from the yaml output
  $("#regionOutput").text(
    `- !Region\n${yamlStr
      .split("\n")
      .map((line) => "  " + line)
      .join("\n")}`
  );
}

function loadExampleRegions() {
  // load example regions
  var container = $(".load-region-examples-container");
  files = [
    "illumina_p5.rgn.yaml",
    "illumina_p7.rgn.yaml",
    "truseq_r1.rgn.yaml",
    "truseq_r2.rgn.yaml",
    "nextera_r1.rgn.yaml",
    "nextera_r2.rgn.yaml",
    "umi.rgn.yaml",
  ];
  files.forEach(function (file) {
    var filePath = "regions/" + file;
    var button = $("<button>")
      .addClass("loadRegionBtn")
      .attr("data-file-path", filePath)
      .text(file.split(".")[0]); // Removes the file extension for the button text
    container.append(button);
  });

  $(".loadRegionBtn").click(function () {
    console.log($(this).data("file-path"));
    var filePath = $(this).data("file-path"); // Retrieve the file path from the button

    $.ajax({
      url: filePath, // Use the file path to load the file
      dataType: "text", // Expecting a YAML/text response
      success: function (data) {
        // Assuming 'data' contains the YAML file content
        data = data.replace(/- !Region/g, ""); // Remove the YAML tag
        var fileContent = jsyaml.load(data); // Convert YAML string to JavaScript object

        // Populate the form
        $("#region_id").val(fileContent.region_id);
        $("#region_type").val(fileContent.region_type);
        $("#name").val(fileContent.name);
        $("#sequence_type").val(fileContent.sequence_type);
        $("#sequence").val(fileContent.sequence);
        $("#min_len").val(fileContent.min_len);
        $("#max_len").val(fileContent.max_len);
        // handle onlist
        if (fileContent.onlist) {
          $("#onlist_location").val(fileContent.onlist.location);
          $("#onlist_filename").val(fileContent.onlist.filename);
          $("#onlist_md5").val(fileContent.onlist.md5);
        }

        // Automatically generate and display the YAML
        generateRegion(); // This calls the previously defined generateRegion function
      },
      error: function (xhr, status, error) {
        console.error("Error loading file:", status, error);
      },
    });
  });
}
