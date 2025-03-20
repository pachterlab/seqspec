import yaml


class File(yaml.YAMLObject):
    yaml_tag = "!File"

    def __init__(
        self,
        file_id: str,
        filename: str,
        filetype: str,
        filesize: int,
        url: str,
        urltype: str,
        md5: str,
    ) -> None:
        super().__init__()
        self.file_id = file_id
        self.filename = filename
        self.filetype = filetype
        self.filesize = filesize
        self.url = url
        self.urltype = urltype
        self.md5 = md5

    def __repr__(self) -> str:
        d = self.to_dict()
        return f"{d}"

    def to_dict(self):
        d = {
            "file_id": self.file_id,
            "filename": self.filename,
            "filetype": self.filetype,
            "filesize": self.filesize,
            "url": self.url,
            "urltype": self.urltype,
            "md5": self.md5,
        }
        return d

    def update_file_id(self, file_id):
        self.file_id = file_id
