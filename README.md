# GTDB Precurate

[![PyPI](https://img.shields.io/pypi/v/gtdb_precurate.svg)](https://pypi.python.org/pypi/gtdb_precurate)

`gtdb_precurate` is an internally used tool used that provides automatic pre-curation of GTDB trees.

## Installation

gtdb_precurate is available on PyPI and can be installed with pip:

```bash
pip install gtdb_precurate
```

## Usage

After a successful install, the `gtdb_precurate` command should be available.

The following positional arguments are required:

* `metadata` - This is the path to the metadata file, it should contain a header as the first line.
    The only requirement is that it has the following columns: `formatted_accession` and `ncbi_wgs_formatted`.
* `red_dict` - This is the path to the RED dictionary output by PhyloRank.
* `red_decorated_tree` - This is the path to the scaled RED decorated output by PhyloRank.
* `out_directory` - This is the path to the directory where the output files will be written.

The following optional arguments are available:

* `--min-bootstrap` - This is the minimum bootstrap value to consider a node to be supported. Default: 95.0.
* `--debug` - This enables debug logging. Default: False.
