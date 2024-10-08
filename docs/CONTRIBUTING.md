---
title: Contributing
date: 2024-06-25
authors:
  - name: A. Sina Booeshaghi
---

# Contributing

Thank you for wanting to add a spec or improve `seqspec`. If you have a bug that is related to `seqspec` please create an issue. This document outlines the process for suggesting improvements to the `seqspec` specification and the procedure for updating the specification.

## Issues

The issue should contain

- the `seqspec` command ran,
- the error message, and
- the `seqspec` and python version.

## Improvements

To suggest improvements to the seqspec project please do the following:

- **Open an Issue**: For suggesting improvements, please open a new issue in the GitHub repository.
- **Describe Your Suggestion**: Clearly describe the problem and your proposed solution. Include examples and use cases where possible.
- **Engagement**: Encourage community feedback on the suggestion through comments.
- **Iterate**: Be open to iterating on your suggestion based on community feedback.

## Specs and code changes

If you'd like to add assays sequence specifications or make modifications to the `seqspec` tool please do the following:

1. Fork the project.

```
# Press "Fork" at the top right of the GitHub page
```

2. Clone the fork and create a branch for your feature

```bash
git clone https://github.com/<USERNAME>/seqspec.git
cd seqspec
git checkout -b cool-new-feature
pip install -r dev-requirements.txt
pre-commit install
```

3. Make changes, add files, and commit

This means creating a `seqspec` for the assay and including one million reads for the FASTQ files pointed to in the spec. Assay specs should be located in `assays/MYASSAY/`. File structure should look like:

```bash
MYASSAY
├── onlist.txt.gz
├── ...
├── spec.yaml
└── fastqs
    ├── R1.fastq.gz
    ├── R2.fastq.gz
    └── ...
```

To generate one million reads from the FASTQ files associated with your spec, the following cna be run:

```bash
zcat allreads_R1.fastq.gz | head -4000000 | gzip > R1.fastq.gz # fastq files has 4 lines per record so 1 million records = 4 million lines
```

Before committing the spec, make sure to run:

```bash
seqspec print spec.yaml # make sure the structure matches expected
secspec check spec.yaml # checks the seqspec against the defined specification
seqspec format -o fmt.yaml spec.yaml  # formats many of the empty fields
mv fmt.yaml spec.yaml # move the formatted spec to the spec.yaml
```

```bash
# make changes, add files, and commit them
git add onlist.txt.gz spec.yaml fastq/R1.fastq.gz fastq/R2.fastq.gz
git commit -m "I made these changes"
```

4. Push changes to GitHub

```bash
git push origin cool-new-feature
```

5. Submit a pull request

If you are unfamiliar with pull requests, you can find more information on the [GitHub help page.](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)

### Steps for Review

1. **Initial Review**: A maintainer will review the suggestion for completeness and relevance.
2. **Community Feedback**: A period for community feedback will follow.
3. **Final Review**: The maintainers will make a final review, considering all feedback.

### Decision Making

- Decisions will be made based on the specification's goals, community feedback, and overall impact on the `seqspec` ecosystem.

## Updating the Specification

### Approval and Merging

- Once approved, a maintainer will merge the changes into the specification.
- Major changes may require a more detailed review process or a community vote.

### Versioning and Change Log

- **Versioning**: Follow semantic versioning. Major changes result in a version bump.
- **Change Log**: Update the change log with a summary of the changes and contributors.

### Testing and Validation

- Ensure any changes are tested for compatibility and do not break existing functionality.

## Adding or modifying controlled vocabulary

Various `Region` attributes use controlled vocabulary to describe the sequence. These vocabulary are listed in the [specification](SPECIFICAITON.md). If you wish to add new controlled vocabulary or modify existing controlled vocabulary please first review the specification and then submit a pull request with an example `Region`. Please justify the inclusion of the controlled vocabulary in your pull request. Below are a list of questions and prompts to address:

If you are suggesting a new `region_type`:

1. In what assay is this `region_type` used? Please link to primary sources.
2. In what ways will the identification and extraction of the `region_type` be useful for sequence processing?
3. What `seqspec` tools need to be modified to take advantage of this new `region_type`?

If you are suggesting a new `sequence_type`:

1. Given examples of this sequence type.
2. Where is this sequence type used?
3. What `seqspec` tools need to be modified to take advantage of this new `sequence_type`?

## Conclusion

We value your contributions and aim to make the process of improving the specification collaborative and transparent. For any questions, please contact the repository maintainers.
