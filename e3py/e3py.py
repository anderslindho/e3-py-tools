#!/usr/bin/env python3
"""
Python utility to interact with e3.

Requires a python-gitlab configuration file (e.g. ~/.python-gitlab.cfg) with 'ess-config' defined.
"""

import sys
from argparse import ArgumentParser

import gitlab

from e3py.core import env, group, module  # noqa: F401


def parse_args():
    parser = ArgumentParser(description="Python utility to interact with e3.")
    subparsers = parser.add_subparsers(dest="command", title="subcommands")

    group_parser = subparsers.add_parser("group", help="e3 gitlab group commands")
    gp_group = group_parser.add_mutually_exclusive_group()
    gp_group.add_argument("name", nargs="?")
    gp_group.add_argument(
        "--all", dest="_all", action="store_true", help="list all groups"
    )
    group_parser.add_argument(
        "--modules", action="store_true", help="list all modules in group"
    )

    module_parser = subparsers.add_parser("module", help="e3 gitlab module commands")
    mp_group = module_parser.add_mutually_exclusive_group()
    mp_group.add_argument("name", nargs="?")
    mp_group.add_argument(
        "--all", dest="_all", action="store_true", help="list all modules"
    )
    module_parser.add_argument(
        "--git-url", action="store_true", help="get url for module"
    )
    module_parser.add_argument(
        "--tags", action="store_true", help="list tags for module"
    )

    env_parser = subparsers.add_parser("env", help="e3 environment commands")
    ep_group = env_parser.add_mutually_exclusive_group()
    ep_group.add_argument("name", nargs="?")
    ep_group.add_argument(
        "--all", dest="_all", action="store_true", help="show module versions"
    )
    env_parser.add_argument("--meta", action="store_true", help="print module metadata")

    return parser.parse_args()


def main():
    args = parse_args()
    gl = gitlab.Gitlab.from_config("ess-gitlab")

    kwargs = vars(args)
    if kwargs["command"] != "env":
        kwargs["gl"] = gl
    try:
        globals()[kwargs.pop("command")](**kwargs)
    except KeyError:
        args.print_help()
        sys.exit(1)


if __name__ == "__main__":
    if sys.version_info < (3, 6, 0):
        sys.stderr.write("You need python 3.6 or later to run this script\n")
        sys.exit(-1)

    main()
