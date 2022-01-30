from typing import Optional, List, Dict
import yaml


# todo figure out how to do enums type options
class Region(yaml.YAMLObject):
    yaml_tag = u'!Region'

    def __init__(self,
                 name: str,
                 sequence_type: str,
                 sequence: str = "",
                 min_len: int = 1,
                 max_len: int = 100,
                 onlist: Optional[str] = None,
                 join: Optional['Join'] = None) -> None:
        super().__init__()
        self.name = name
        self.sequence_type = sequence_type
        self.sequence = sequence

        self.min_len = min_len
        self.max_len = max_len

        self.onlist = onlist
        self.join = join

        if self.join:
            self.min_len, self.max_len = self.get_len()
            self.max_len += 1

            self.sequence = self.get_sequence()

    def get_sequence(self, s: str = "") -> str:
        if self.join:
            for n, r in self.join.regions.items():
                s = r.get_sequence(s)
        else:
            if self.sequence:
                s += self.sequence
            elif self.sequence is None:
                s += "X"
        return s

    def get_len(self, min_l: int = 0, max_l: int = 0):
        if self.join:
            for n, r in self.join.regions.items():
                min_l, max_l = r.get_len(min_l, max_l)
        else:
            min_l += self.min_len
            max_l += self.max_len - 1
        return (min_l, max_l)

    def update_attr(self):
        if self.join:
            for n, r in self.join.regions.items():
                r.update_attr()

        self.sequence = self.get_sequence()
        self.min_len, self.max_len = self.get_len()
        return

    def __repr__(self) -> str:
        d = {
            "sequence_type": self.sequence_type,
            "onlist": self.onlist,
            "sequence": self.sequence,
            "min_len": self.min_len,
            "max_len": self.max_len,
            "join": self.join
        }
        return f"{d}"


class Join(yaml.YAMLObject):
    yaml_tag = u'!Join'

    def __init__(
        self,
        how: str,
        order: List[str],
        regions: Dict[str, Region],
    ) -> None:
        super().__init__()
        self.regions = regions
        self.how = how
        self.order = order

    def __repr__(self) -> str:
        d = {
            "how": self.how,
            "order": self.order,
            "regions": self.regions,
        }
        return f"{d}"