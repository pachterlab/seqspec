from seqspec.Assay import Assay
import yaml


def main():
    s = "STRT-seq-C1"
    fn = f"examples/{s}/spec.yaml"
    with open(fn, 'r') as stream:
        data: Assay = yaml.load(stream, Loader=yaml.Loader)
    data.update_spec()
    data.to_YAML("./test.yaml")


if __name__ == "__main__":
    main()
