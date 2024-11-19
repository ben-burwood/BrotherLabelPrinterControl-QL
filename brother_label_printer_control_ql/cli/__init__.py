import logging

import click

from .analyse import analyze_cmd
from .discover import discover
from .info import info
from .print import print_cmd
from .send import send_cmd
from ..backends import Backend
from ..models import Models

logger = logging.getLogger("brother_ql")


printer_help = "The identifier for the printer. This could be a string like tcp://192.168.1.21:9100 for a networked printer or usb://0x04f9:0x2015/000M6Z401370 for a printer connected via USB."


@click.group()
@click.option("-b", "--backend", type=click.Choice(Backend.all()), envvar="BROTHER_QL_BACKEND")
@click.option("-m", "--model", type=click.Choice(Models.identifiers()), envvar="BROTHER_QL_MODEL")
@click.option("-p", "--printer", metavar="PRINTER_IDENTIFIER", envvar="BROTHER_QL_PRINTER", help=printer_help)
@click.option("--debug", is_flag=True)
@click.version_option()
@click.pass_context
def cli(ctx, *args, **kwargs):
    """Command line interface for the brother_ql Python package."""

    backend = kwargs.get("backend", None)
    model = kwargs.get("model", None)
    printer = kwargs.get("printer", None)
    debug = kwargs.get("debug")

    # Store the general CLI options in the context meta dictionary.
    # The name corresponds to the second half of the respective envvar:
    ctx.meta["MODEL"] = model
    ctx.meta["BACKEND"] = backend
    ctx.meta["PRINTER"] = printer

    logging.basicConfig(level="DEBUG" if debug else "INFO")


cli.add_command(discover)
cli.add_command(info)
cli.add_command(print_cmd)
cli.add_command(analyze_cmd)
cli.add_command(send_cmd)

if __name__ == "__main__":
    cli()
