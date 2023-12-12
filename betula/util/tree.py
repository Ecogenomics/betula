import dendropy


def parse_node_label(node: dendropy.Node):
    bs = None
    taxon = None

    # Leaf node, return nothing
    if node.is_leaf():
        gid, red = node.taxon.label.split('|RED=')
        red = float(red)
        bs = None
        taxon = None
        return red, bs, taxon

    # Dummy node for leaf nodes, extract taxon and return RED
    else:
        label = node.label

        # Extract the RED that will always be present
        prefix, suffix = label.split('|RED=')
        red = float(suffix)

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
