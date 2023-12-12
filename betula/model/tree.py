from collections import defaultdict, deque
from pathlib import Path
from typing import Set, Dict, FrozenSet, Iterator

import dendropy

from betula.model.node_label import NodeLabel
from betula.model.ranks import RANKS, TaxString
from betula.util.tree import parse_node_label


class Tree:

    def __init__(self, tree):
        self.data: dendropy.Tree = tree

        # Pre-compute values required
        self.gids: Set[str] = self.get_gids()
        self.node_depths: Dict[int, FrozenSet[dendropy.Node]] = self.get_node_depths()
        self.node_descs: Dict[dendropy.Node, FrozenSet[dendropy.Node]] = self.get_node_descs()
        self.known_taxa: FrozenSet[str] = self.get_tree_taxa()

    def get_gids(self) -> Set[str]:
        out = set()
        for taxon in self.data.taxon_namespace:
            label = taxon.label
            if label.startswith('G'):
                out.add(label.split('|')[0])
        return out

    def get_node_depths(self):
        """Compute the depth of each node in the tree."""
        out = defaultdict(set)
        queue = deque([(self.data.seed_node, 0)])
        while len(queue) > 0:
            cur_node, cur_depth = queue.popleft()
            out[cur_depth].add(cur_node)
            for child_node in cur_node.child_nodes():
                queue.append((child_node, cur_depth + 1))
        return {k: frozenset(v) for k, v in out.items()}

    def get_node_descs(self):
        """Calculate the descendants of each node in the tree."""
        out = defaultdict(set)
        max_depth = max(self.node_depths.keys())
        for i in reversed(range(max_depth + 1)):
            for cur_node in self.node_depths[i]:
                if cur_node.is_leaf():
                    out[cur_node] = set()
                else:
                    for child_node in cur_node.child_node_iter():
                        out[cur_node].update(out[child_node])
                        out[cur_node].add(child_node)
        return {k: frozenset(v) for k, v in out.items()}

    def get_node_ancestors(self, node: dendropy.Node) -> Iterator[dendropy.Node]:
        """Returns all ancestors of the specified node."""
        cur_node = node.parent_node
        while cur_node is not None:
            yield cur_node
            cur_node = cur_node.parent_node

    def get_tree_taxa(self) -> FrozenSet[str]:
        """Generates a set of all taxa observed in the tree."""
        out = set()
        for node in self.data.postorder_node_iter():
            _, _, taxa = parse_node_label(node)
            if taxa is not None:
                for taxon in taxa.split('; '):
                    out.add(taxon)
        return frozenset(out)

    def remove_red_labels(self):
        for node in self.data.postorder_node_iter():
            if node.is_leaf():
                node.taxon.label = node.taxon.label.split('|')[0]
            else:
                node.label = node.label.split('|')[0]
        return

    def infer_gid_taxstring_from_tree(self) -> Dict[dendropy.Node, TaxString]:
        out = dict()
        for leaf_node in self.data.leaf_node_iter():
            if not leaf_node.taxon.label.startswith('G'):
                continue
            tax_string = defaultdict(list)
            for ancestor in self.get_node_ancestors(leaf_node):
                label = NodeLabel(ancestor)
                if label.taxon is not None:
                    for cur_taxon in label.taxon.split('; '):
                        tax_string[cur_taxon[0]].append(cur_taxon)
            out[leaf_node] = TaxString.from_dict(tax_string)
        return out

    def get_ranks_below_node(self, node: dendropy.Node) -> FrozenSet[str]:
        out = set()
        for desc_node in self.node_descs[node]:
            label = NodeLabel(desc_node)
            if label.taxon is not None:
                for taxon in label.taxon.split('; '):
                    out.add(taxon[0])
        return frozenset(out)

    def get_ranks_above_node(self, node: dendropy.Node) -> FrozenSet[str]:
        out = set()
        for ancestor in self.get_node_ancestors(node):
            label = NodeLabel(ancestor)
            if label.taxon is not None:
                for taxon in label.taxon.split('; '):
                    out.add(taxon[0])
        return frozenset(out)

    def add_taxon_to_node(self, node: dendropy.Node, taxon: str):
        label = NodeLabel(node)

        # Sort the new ranks, deal with the case that one may exist
        new_tax_dict = {taxon[0]: taxon}
        if label.taxon is not None:
            for cur_taxon in label.taxon.split('; '):
                cur_rank = cur_taxon[0]
                assert cur_rank not in new_tax_dict
                new_tax_dict[cur_rank] = cur_taxon
        new_tax_string = list()
        for cur_rank, the_taxon in sorted(new_tax_dict.items(), key=lambda x: RANKS.index(x[0])):
            new_tax_string.append(the_taxon)
        new_tax_string = '; '.join(new_tax_string)

        # This is a species label node
        if label.bs is None:
            new_taxon_next_label = f'{new_tax_string}|RED={label.red:.3f}'
        else:
            new_taxon_next_label = f'{label.bs:.1f}:{new_tax_string}|RED={label.red:.3f}'

        node.label = new_taxon_next_label
        return

    @classmethod
    def load(cls, path: Path):
        tree = dendropy.Tree.get(path=path, schema="newick", preserve_underscores=True)
        return cls(tree)

    def write(self, path: Path):
        self.data.write(path=path, schema="newick", suppress_rooting=True)
