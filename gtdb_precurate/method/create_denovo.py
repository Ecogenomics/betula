import logging
from collections import defaultdict

from gtdb_precurate.model.metadata import MetadataFile
from gtdb_precurate.model.node_label import NodeLabel
from gtdb_precurate.model.ranks import RANKS
from gtdb_precurate.model.red_dict import RedDict
from gtdb_precurate.model.tree import Tree


def get_gids_missing_ranks(tree):
    out = dict()
    for leaf_node, tax_string in tree.infer_gid_taxstring_from_tree().items():

        # We want to only subset this to those leaf nodes what are new
        parent_label = NodeLabel(leaf_node.parent_node)
        if parent_label.taxon is not None and 'unresolved' in parent_label.taxon:
            missing_ranks = tax_string.missing_ranks()
            if len(missing_ranks) > 0:
                out[leaf_node] = missing_ranks
    return out


def get_candidate_nodes_for_missing_ranks(tree, d_leaf_to_missing_ranks, min_bootstrap, red):
    out = defaultdict(dict)
    d_failed = defaultdict(set)
    for leaf_node, missing_ranks in d_leaf_to_missing_ranks.items():

        # Additionally, we want to look up the tree to avoid nesting higher ranks
        cur_ancestor_ranks = tree.get_ranks_above_node(leaf_node) - {'s'}
        cur_ancestor_ranks_sorted = sorted(cur_ancestor_ranks, key=lambda x: RANKS.index(x))
        new_rank_must_be_above_idx = RANKS.index(cur_ancestor_ranks_sorted[-1])

        # Duplicate work, but we want to check it from the highest to lowest rank
        for cur_rank in missing_ranks:

            # Check to see if adding this rank would cause a nesting of higher ranks
            if RANKS.index(cur_rank) <= new_rank_must_be_above_idx:
                d_failed[leaf_node].add(cur_rank)
                break

            red_threshold = red.get_rank_threshold(cur_rank)

            for ancestor in tree.get_node_ancestors(leaf_node):

                # Before checking anything relating to RED/bootstraps, we need
                # to make sure that adding a rank at this node would not
                # cause any conflicts
                cur_desc_ranks = tree.get_ranks_below_node(ancestor)
                if cur_rank in cur_desc_ranks:
                    break

                # Otherwise, check RED/bs
                label = NodeLabel(ancestor)

                # No bootstrap value is a dummy node artifact
                bs_supported = label.bs is None or label.bs >= min_bootstrap

                # Calculate the red threshold
                red_supported = label.red >= red_threshold

                # As we will never have this supported, stop going up
                if not red_supported:
                    break

                # Otherwise, cache this candidate node
                if bs_supported and red_supported:
                    out[cur_rank][leaf_node] = ancestor

            # Do a quick check to see if we were able to obtain a candidate
            if out[cur_rank].get(leaf_node) is None:
                d_failed[leaf_node].add(cur_rank)
    return out, d_failed


BAD_PAIRS = [("I", "L"), ("0", "O"), ("1", "I"), ("5", "S"), ("2", "Z")]


def score_candidate_taxon(taxon):
    for a, b in BAD_PAIRS:
        if a in taxon and b in taxon:
            return 1
    return 0


def create_taxon(rank, meta, new_taxa, tree, gids):
    prohibited_taxa = new_taxa.union(tree.known_taxa)
    wgs_available = set()
    for gid in gids:
        wgs = meta.data[gid]
        if wgs is not None:
            wgs_rank = f'{rank}__{wgs}'
            if wgs_rank not in prohibited_taxa:
                wgs_available.add(wgs_rank)

    # No WGS can be used, just use the first genome id
    if len(wgs_available) == 0:
        first_gid = sorted(gids)[0]
        return f'{rank}__{first_gid}'

    # Otherwise, take the "best" sscoring WGS
    taxa_sorted = sorted(wgs_available, key=lambda x: (score_candidate_taxon(x), x))
    return taxa_sorted[0]


def create_ranks(d_rank_to_leaf_candidates, tree, meta):
    # We will now iterate from the highest to lower rank to find shared nodes
    created = set()
    log = logging.getLogger('gtdb_precurate')
    for cur_rank, d_leaf_to_candidate_node in sorted(d_rank_to_leaf_candidates.items(),
                                                     key=lambda x: RANKS.index(x[0])):

        # We need to find the shared nodes
        d_shared_nodes = defaultdict(set)
        for leaf_node, candidate_node in d_leaf_to_candidate_node.items():
            d_shared_nodes[candidate_node].add(leaf_node)

        log.info(
            f'Found {len(d_shared_nodes):,} nodes for node placement at rank {cur_rank}, representing ({len(d_leaf_to_candidate_node):,} genomes)')

        # Now, we need to find the shared nodes that have the same number of
        # leaf nodes as the number of genomes that are missing this rank
        for shared_node, leaf_nodes in d_shared_nodes.items():
            # What are the genome accessions for these leaf nodes?
            leaf_node_gids = {x.taxon.label.split('|')[0] for x in leaf_nodes}

            # Create the taxon and make it off-limits
            new_taxon = create_taxon(cur_rank, meta, created, tree, leaf_node_gids)
            created.add(new_taxon)

            # Update the tree to have this taxon
            tree.add_taxon_to_node(shared_node, new_taxon)

    return frozenset(created)


def create_denovo_clusters(
        tree: Tree,
        meta: MetadataFile,
        red: RedDict,
        min_bootstrap: float
):
    """Creates de novo clusters from the specified tree and metadata."""

    log = logging.getLogger('gtdb_precurate')

    # First, we need to find all genomes that are missing ranks
    d_leaf_to_missing_ranks = get_gids_missing_ranks(tree)
    log.info(f'Found {len(d_leaf_to_missing_ranks):,} unresolved genomes missing one or more ranks')

    # Now, we need to find the candidate nodes for each of these leaf nodes
    d_rank_to_leaf_candidates, d_leaf_to_missing_candidate_rank = get_candidate_nodes_for_missing_ranks(
        tree,
        d_leaf_to_missing_ranks,
        min_bootstrap,
        red
    )
    if len(d_leaf_to_missing_candidate_rank) > 0:
        log.warning(f'Unable to candidate nodes for {len(d_leaf_to_missing_candidate_rank):,} genomes')

    created = create_ranks(d_rank_to_leaf_candidates, tree, meta)

    return created
