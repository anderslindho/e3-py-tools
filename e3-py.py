#!/usr/bin/env python3
"""
Python utility to download and install modules.

Requires a python-gitlab configuration file (e.g. ~/.python-gitlab.cfg) with 'ess-config' defined.
"""

# import subprocess
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
from pprint import pprint

import gitlab

# todo: move to config ?
E3_GROUP_ID = 215


def parse_args():
    parser = ArgumentParser(
        description="Python utility to download and install modules."
    )
    subparsers = parser.add_subparsers(
        dest="command", help="command to execute"
    )  # this line changed

    list_parser = subparsers.add_parser("list")
    list_mutex_group = list_parser.add_mutually_exclusive_group()
    list_mutex_group.add_argument("group", nargs="?", help="group to list modules in")
    list_mutex_group.add_argument(
        "--groups", action="store_true", help="show module groups"
    )
    list_mutex_group.add_argument(
        "--all", action="store_true", help="show modules in all groups"
    )

    module_parser = subparsers.add_parser("module")
    module_parser.add_argument("module")
    module_parser.add_argument("--clone", action="store_true", help="clone module")

    env_parser = subparsers.add_parser("env")
    env_mutex_group = env_parser.add_mutually_exclusive_group()
    env_mutex_group.add_argument(
        "module", nargs="?", help="list available versions of module"
    )
    env_mutex_group.add_argument(
        "--all", action="store_true", help="show all loaded modules"
    )

    # todo: add 'admin' command to call on protect scripts (?)

    return parser.parse_args()


def main():
    args = parse_args()

    gl = gitlab.Gitlab.from_config("ess-gitlab")
    e3 = gl.groups.get(E3_GROUP_ID)

    config = ConfigParser(allow_no_value=True)
    config.read("e3-config.ini")
    excluded_groups = set(_ for _ in config["excluded_groups"])
    excluded_projects = set(_ for _ in config["excluded_projects"])

    groups = {
        group.path: group.id
        for group in e3.subgroups.list(all=True)
        if group.name not in excluded_groups
    }
    projects = [project for project in e3.projects.list(all=True)]
    for name, _id in groups.items():
        group = gl.groups.get(_id)
        projects.extend(project for project in group.projects.list(all=True))

    if args.command == "list":
        # todo: refactor
        if args.all:
            _projects = set(project.name for project in projects)
            _projects = sorted(_projects - excluded_projects)
            print(f"There are {len(_projects)} projects:")
            for project in _projects:
                print(project)

        elif args.groups:
            print(f"There are {len(groups)} groups:")
            for group in groups:
                print(f"{group}")

        elif args.group:
            group_id = groups[args.group]
            group = gl.groups.get(group_id)
            _projects = group.projects.list(all=True)
            print(
                f"The group {args.group} contains the following {len(_projects)} modules:"
            )
            for project in _projects:
                print(project.name)

    elif args.command == "module":
        projects_dict = {project.name.lower(): project.id for project in projects}
        try:
            project_id = projects_dict[f"e3-{args.module}"]
        except KeyError:
            print(f"Module {args.module} does not exist")
            sys.exit(-1)
        project = gl.projects.get(project_id)
        if args.clone:
            pass
            # todo: figure out how to keep track of relevant projects; load at runtime?
            # if args.module in projects:
            # project = [project.id for project in projects if project.name == args.args][0]
            # git_url = project.ssh_url_to_repo
            # subprocess.call(['git', 'clone', git_url])
            # else:
            # print(f"{args.args} does not exist")
        else:
            pprint(project.attributes, indent=2)

    elif args.command == "env":
        # print local e3 env from environment vars
        # maybe use treelib
        if args.module:
            # try to find module, print versions
            # also be able to print dependencies and meta.yaml
            pass
        elif args.all:
            pass


if __name__ == "__main__":
    if sys.version_info < (3, 6, 0):
        sys.stderr.write("You need python 3.6 or later to run this script\n")
        sys.exit(1)

    main()
