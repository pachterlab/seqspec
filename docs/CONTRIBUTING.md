## Contributing

Thank you for wanting to add a spec or improve `seqspec`. If you have a bug that is related to `seqspec` please create an issue.

### Issues

The issue should contain

- the `seqspec` command ran,
- the error message, and
- the `seqspec` and python version.

### Specs and code changes

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
zcat allreads_R1.fastq.gz | head -4000000 | gzip > R1.fastq.gz # fastq files has 4 lines per record so 1 million records = 4 milllion lines
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

If you are unfamilar with pull requests, you can find more information on the [GitHub help page.](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)
