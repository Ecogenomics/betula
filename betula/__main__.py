import sys
from pathlib import Path

import typer

from betula import __version__
from betula.method.create_denovo import create_denovo_clusters
from betula.model.metadata import MetadataFile
from betula.model.ranks import RANKS
from betula.model.red_dict import RedDict
from betula.model.tree import Tree
from betula.util.logger import init_logger


def main(
        metadata: Path,
        red_dict: Path,
        red_decorated_tree: Path,
        out_directory: Path,
        min_bootstrap: float = 95.0,
        debug: bool = False
):
    # Create the output directory
    out_directory.mkdir(parents=True, exist_ok=True)

    # Initialise the logger
    log = init_logger(out_directory, debug)
    log.info(f'betula v{__version__}')
    log.info(f'betula {" ".join(sys.argv[1:])}')

    # Create the output paths
    if 'red_decorated' in red_decorated_tree.name:
        tree_path_out = out_directory / red_decorated_tree.name.replace('red_decorated', 'betula')
    else:
        tree_path_out = out_directory / f'{red_decorated_tree.stem}.betula{red_decorated_tree.suffix}'
    report_path_out = out_directory / f'{tree_path_out.stem}_report.tsv'

    # Read the RED dictionary
    log.info(f'Loading RED dictionary: {red_dict.name}')
    red = RedDict.load(red_dict)

    log.info(f'Reading tree: {red_decorated_tree.name}')
    tree = Tree.load(red_decorated_tree)
    log.info(f'Found {len(tree.gids):,} genomes (excluding zombies)')

    log.info(f'Loading metadata: {metadata.name}')
    meta = MetadataFile.load(metadata, gids_required=tree.gids)
    log.info(f'Found {len(meta.data):,} corresponding records')

    log.info('Inferring de novo clusters')
    created = create_denovo_clusters(tree, meta, red, min_bootstrap)

    log.info(f'Removing RED labels from the tree')
    tree.remove_red_labels()

    log.info(f'Writing tree to disk: {tree_path_out}')
    tree.write(tree_path_out)

    log.info(f'Writing report to disk: {report_path_out}')
    with report_path_out.open('w') as f:
        for cur_taxon in sorted(created, key=lambda x: RANKS.index(x[0])):
            f.write(f'{cur_taxon}\n')

    log.info('Done.')

    return


if __name__ == '__main__':
    typer.run(main)
