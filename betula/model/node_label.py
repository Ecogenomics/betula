from typing import Optional

import dendropy


class NodeLabel:
    __slots__ = ('red', 'bs', 'taxon')

    def __init__(self, node: dendropy.Node):
        red, bs, taxon = self.parse_node_label(node)
        self.red: float = red
        self.bs: Optional[float] = bs
        self.taxon: Optional[str] = taxon

    @staticmethod
    def parse_node_label(node: dendropy.Node):
        # Leaf node, return nothing
        if node.is_leaf():
            _, red = node.taxon.label.split('|RED=')
            return float(red), None, None

        # Internal node, may have all three
        else:

            # Extract the RED that will always be present
            prefix, suffix = node.label.split('|RED=')
            red = float(suffix)
            bs = None
            taxon = None

            # Extract either the taxon or the bootstrap + taxon
            if ':' in prefix:
                bs, taxon = prefix.split(':')
                bs = float(bs)
            else:
                try:
                    bs = float(prefix)
                except ValueError:
                    taxon = prefix
            return red, bs, taxon
