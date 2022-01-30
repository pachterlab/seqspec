import yaml
from typing import Dict, List

from seqspec.Region import Join, Region


class Protocol(Join):
    yaml_tag = u'!Protocol'

    def __init__(self, how: str, order: List[str],
                 regions: Dict[str, Region]) -> None:
        super().__init__(how, order, regions)
        pass
