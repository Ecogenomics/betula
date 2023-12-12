import json
from pathlib import Path

from gtdb_precurate.model.ranks import RANKS


class RedDict:
    __slots__ = ('d', 'p', 'c', 'o', 'f', 'g', 's')

    def __init__(self, d, p, c, o, f, g, s):
        self.d: float = d
        self.p: float = p
        self.c: float = c
        self.o: float = o
        self.f: float = f
        self.g: float = g
        self.s: float = s
        return

    def get_rank(self, rank_str: str):
        """Returns the RED value for the current rank."""
        return getattr(self, rank_str)

    def get_rank_higher(self, rank_str: str):
        """Returns the RED value for the parent rank."""
        parent_rank = RANKS[RANKS.index(rank_str) - 1]
        return self.get_rank(parent_rank)

    def get_rank_threshold(self, rank: str):
        """Compute the halfway point between the current rank and parent."""
        cur_rank = self.get_rank(rank)
        parent_rank = self.get_rank_higher(rank)
        return (cur_rank + parent_rank) / 2.0

    @classmethod
    def load(cls, path: Path):
        with open(path) as f:
            val = json.loads(f.read())
            new = {k[0]: v for k, v in val.items()}
            new['d'] = 0.0
            return cls(**new)
