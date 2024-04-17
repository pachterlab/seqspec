// Define the Assay class
class Assay {
  constructor({
    seqspec_version,
    assay_id,
    name,
    doi,
    date,
    description,
    modalities,
    lib_struct,
    library_protocol,
    library_kit,
    sequence_protocol,
    sequence_kit,
    sequence_spec,
    library_spec,
  }) {
    this.seqspec_version = seqspec_version;
    this.assay_id = assay_id;
    this.name = name;
    this.doi = doi;
    this.date = date;
    this.description = description;
    this.modalities = modalities;
    this.lib_struct = lib_struct;
    this.sequence_kit = sequence_kit;
    this.sequence_protocol = sequence_protocol;
    this.library_kit = library_kit;
    this.library_protocol = library_protocol;
    this.sequence_spec = sequence_spec.map((spec) => new Read(spec));
    this.library_spec = library_spec.map((spec) => new Region(spec));
  }
}

// Define the Read class
class Read {
  constructor({
    read_id,
    name,
    modality,
    primer_id,
    min_len,
    max_len,
    strand,
  }) {
    this.read_id = read_id;
    this.name = name;
    this.modality = modality;
    this.primer_id = primer_id;
    this.min_len = min_len;
    this.max_len = max_len;
    this.strand = strand;
  }
}

// Define the Region class
class Region {
  constructor({
    region_id,
    region_type,
    name,
    sequence_type,
    sequence,
    min_len,
    max_len,
    onlist,
    regions,
    parent_id,
  }) {
    this.region_id = region_id;
    this.region_type = region_type;
    this.name = name;
    this.sequence_type = sequence_type;
    this.sequence = sequence;
    this.min_len = min_len;
    this.max_len = max_len;
    this.onlist = onlist ? new Onlist(onlist) : null;
    this.regions = regions ? regions.map((region) => new Region(region)) : [];
    this.parent_id = parent_id;
  }
}

// Define the Onlist class
class Onlist {
  constructor({ filename, md5, location }) {
    this.filename = filename;
    this.md5 = md5;
    this.location = location;
  }
}
