from pathlib import Path
from typing import Dict, Optional, Set


class MetadataFile:
    __slots__ = ('data',)

    def __init__(self, data):
        self.data: Dict[str, str] = data

    @classmethod
    def load(cls, path: Path, gids_required: Optional[Set[str]] = None):
        out = dict()
        with open(path) as f:
            header = f.readline().strip().split('\t')
            header = {k: i for i, k in enumerate(header)}
            for line in f.readlines():
                cols = line.strip().split('\t')
                gid = cols[header['formatted_accession']]

                # If the user has requested a subset, skip if not present
                if gids_required and gid not in gids_required:
                    continue

                wgs_formatted = cols[header['ncbi_wgs_formatted']]
                wgs_formatted = None if wgs_formatted == 'none' else wgs_formatted
                out[gid] = wgs_formatted
        return cls(out)
