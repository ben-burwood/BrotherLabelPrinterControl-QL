import click

from ..backends import Backend
from ..utils.output_helpers import log_discovered_devices


@click.command()
@click.pass_context
def discover(ctx):
    """find connected label printers"""
    backend = Backend(ctx.meta.get("BACKEND", "pyusb"))
    available_devices = backend.discover()

    log_discovered_devices(available_devices)
    print(available_devices)
