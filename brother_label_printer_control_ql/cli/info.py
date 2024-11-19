import platform
import shutil
import sys

import click
from pkg_resources import get_distribution

from ..labels import Labels
from ..models import Models
from ..utils.output_helpers import textual_label_description


@click.group()
@click.pass_context
def info(ctx, *args, **kwargs):
    """List available labels, models etc."""


@info.command(name="models")
@click.pass_context
def models_cmd(ctx, *args, **kwargs):
    """List the choices for --model"""
    print("Supported models:")
    for model in Models.identifiers():
        print(" " + model)


@info.command()
@click.pass_context
def labels(ctx, *args, **kwargs):
    """List the choices for --label"""
    print(textual_label_description([label.value for label in Labels]))


@info.command()
@click.pass_context
def env(ctx, *args, **kwargs):
    """print debug info about running environment"""
    print("\n##################\n")
    print("Information about the running environment of brother_ql.")
    print("(Please provide this information when reporting any issue.)\n")

    # computer
    print("About the computer:")
    for attr in ("platform", "processor", "release", "system", "machine", "architecture"):
        print("  * " + attr.title() + ":", getattr(platform, attr)())

    # Python
    print("About the installed Python version:")
    py_version = str(sys.version).replace("\n", " ")
    print("  *", py_version)

    # brother_ql
    print("About the brother_ql package:")
    pkg = get_distribution("brother_ql")
    print("  * package location:", pkg.location)
    print("  * package version: ", pkg.version)
    try:
        cli_loc = shutil.which("brother_ql")
    except:
        cli_loc = "unknown"
    print("  * brother_ql CLI path:", cli_loc)

    # brother_ql's requirements
    print("About the requirements of brother_ql:")
    fmt = "  {req:14s} | {spec:10s} | {ins_vers:17s}"
    print(fmt.format(req="requirement", spec="requested", ins_vers="installed version"))
    print(fmt.format(req="-" * 14, spec="-" * 10, ins_vers="-" * 17))
    requirements = list(pkg.requires())
    requirements.sort(key=lambda x: x.project_name)
    for req in requirements:
        proj = req.project_name
        req_pkg = get_distribution(proj)
        spec = " ".join(req.specs[0]) if req.specs else "any"
        print(fmt.format(req=proj, spec=spec, ins_vers=req_pkg.version))
    print("\n##################\n")
