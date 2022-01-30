from seqspec.Assay import Assay
import yaml


def main():
    s = "10x-RNA-ATAC"
    fn = f"examples/{s}/spec.yaml"
    with open(fn, 'r') as stream:
        data: Assay = yaml.load(stream, Loader=yaml.Loader)
    data.update_spec()
    data.to_YAML(fn)


if __name__ == "__main__":
    main()
