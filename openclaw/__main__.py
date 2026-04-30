"""openclaw/__main__.py — Entry point for `python -m openclaw` and the `openclaw` CLI command."""

import importlib.util
import os
import sys


def _setup_paths():
    """Put the repo root on sys.path and chdir to it so relative paths work."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    os.chdir(repo_root)
    return repo_root


def _load_cli(repo_root: str):
    """Load the root-level __main__.py as a module without triggering circular import."""
    spec = importlib.util.spec_from_file_location(
        "openclaw_cli", os.path.join(repo_root, "__main__.py")
    )
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli


def main_entry():
    """Called by the `openclaw` console script installed via pip."""
    repo_root = _setup_paths()
    cli = _load_cli(repo_root)
    cli.main()


if __name__ == "__main__":
    main_entry()
