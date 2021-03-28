#!/usr/bin/env python3
"""
Python utility to interact with e3.

Requires a python-gitlab configuration file (e.g. ~/.python-gitlab.cfg) with 'ess-config' defined.
"""

import os
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from pprint import pprint

import gitlab
import yaml

# todo: move to config ?
E3_GROUP_ID = 215
E3_ENV_VARS = [
    "EPICS_BASE",
    "E3_REQUIRE_NAME",
    "E3_REQUIRE_VERSION",
]


def group(gl: gitlab.Gitlab, name: str, _all: bool, modules: bool):
    groups = {
        group.name: group
        for group in gl.groups.get(E3_GROUP_ID).subgroups.list(all=True, lazy=True)
    }

    def get_group(name: str) -> gitlab.v4.objects.Group:
        try:
            group = gl.groups.get(groups[name].id)
        except KeyError:
            group = None
        return group

    if _all:
        print(f"There are {len(groups.keys())} groups:")
        for name in groups.keys():
            print(f"- {name}")
            if modules:
                group = get_group(name)
                for module in group.projects.list(all=True):
                    print(f"{module.name}")
    else:
        if name is None:
            print("You need to specify a group. Aborting.")
            sys.exit(-1)
        group = get_group(name)
        if group is None:
            print(f"Group {name} does not exist. Aborting.")
            sys.exit(-1)
        if modules:
            projects = group.projects.list(all=True, lazy=True)
            print(
                f"The group {group.name} contains the following {len(projects)} modules:"
            )
            for project in projects:
                print(project.name)
        else:
            group = groups[name]
            pprint(group.attributes, indent=2)


def module(gl: gitlab.Gitlab, name: str, _all: bool, git_url: bool, tags: bool):
    projects = {
        project.name: project
        for project in gl.groups.get(E3_GROUP_ID).projects.list(
            all=True, lazy=True, include_subgroups=True
        )
    }

    def get_project() -> gitlab.v4.objects.Project:
        """
        Returns project if one can be found.

        Searches first for exact match, then for with "e3-" prefix added, then any.
        Returns zero matches if there are multiple options.
        """
        try:
            project = gl.projects.get(projects[name].id)
        except KeyError:
            try:
                project = gl.projects.get(projects[f"e3-{name}"].id)
            except KeyError:
                candidate_projects: list = []
                for project_name in projects.keys():
                    if re.search(name, project_name):
                        candidate_projects.append(
                            gl.projects.get(projects[project_name].id)
                        )
                if candidate_projects:
                    if len(candidate_projects) > 1:
                        print("Multiple options match:")
                        for project in candidate_projects:
                            print(f"- {project.name}")
                        project = None
                    else:
                        project = candidate_projects[0]
        return project

    if _all:
        print(f"There are {len(projects.keys())} projects:")
        for project_name in projects.keys():
            print(f"{project_name}")
    else:
        if name is None:
            print("You have to provide a module name with those options. Aborting.")
            sys.exit(-1)
        project = get_project()
        if project is None:
            print(f"No clear match for {name}. Aborting.")
            sys.exit(-1)
        if tags:
            for tag in project.tags.list(all=True):
                print(f"{tag.name}")
        elif git_url:
            print(project.ssh_url_to_repo)
        else:
            pprint(project.attributes, indent=2)


# todo: maybe use treelib?
def env(name: str, _all: bool, meta: bool):
    env_vars = [_ for _ in map(os.environ.get, E3_ENV_VARS)]
    if not all(env_vars):
        print(
            f"You need to source an e3 environment, or set the variables {E3_ENV_VARS}. Aborting."
        )
        sys.exit(-1)

    def print_from_file(filename: Path):
        with open(filename, "r") as f:
            if filename.suffix in (".yml", ".yaml"):
                a_dict = yaml.safe_load(f)
                pprint(a_dict)
            else:
                print(f.read())

    def print_module(directory: Path) -> None:
        module_name = directory.stem
        print(module_name)
        for ver in directory.iterdir():
            print(f"- {os.path.basename(ver)}")
            if meta:
                metadata_file = ver / f"{module_name}_meta.yaml"
                if metadata_file.exists():
                    print_from_file(metadata_file)
                else:
                    print("metadata missing")

    epics_base_path, require_name, require_ver = env_vars
    e3_sitemods_path = Path(epics_base_path) / require_name / require_ver / "siteMods"
    print(e3_sitemods_path.as_posix())
    if _all:
        for module in e3_sitemods_path.iterdir():
            print_module(module)
    else:
        if name is None:
            print("You have to provide a module name with those options. Aborting.")
            sys.exit(-1)
        module = Path(e3_sitemods_path) / name
        print_module(module)


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
        sys.exit(1)


if __name__ == "__main__":
    if sys.version_info < (3, 6, 0):
        sys.stderr.write("You need python 3.6 or later to run this script\n")
        sys.exit(-1)

    main()
