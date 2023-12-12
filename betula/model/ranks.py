from typing import List, Dict, Tuple

RANKS = ('d', 'p', 'c', 'o', 'f', 'g', 's')


class TaxString:
    __slots__ = ('d', 'p', 'c', 'o', 'f', 'g', 's')

    def __init__(self, d, p, c, o, f, g, s):
        self.d: Tuple[str] = tuple(d)
        self.p: Tuple[str] = tuple(p)
        self.c: Tuple[str] = tuple(c)
        self.o: Tuple[str] = tuple(o)
        self.f: Tuple[str] = tuple(f)
        self.g: Tuple[str] = tuple(g)
        self.s: Tuple[str] = tuple(s)

    def __repr__(self):
        return self.as_string()

    @classmethod
    def from_dict(cls, input_d: Dict[str, List[str]]):
        return cls(
            d=input_d['d'],
            p=input_d['p'],
            c=input_d['c'],
            o=input_d['o'],
            f=input_d['f'],
            g=input_d['g'],
            s=input_d['s'],
        )

    def as_string(self) -> str:
        out = list()
        for rank in RANKS:
            cur_val = getattr(self, rank)
            if len(cur_val) == 0:
                out.append(f'{rank}__')
            else:
                out.extend(getattr(self, rank))
        return '; '.join(out)

    def missing_ranks(self) -> Tuple[str]:
        out = list()
        for rank in RANKS:
            if len(getattr(self, rank)) == 0:
                out.append(rank)
        return tuple(out)
