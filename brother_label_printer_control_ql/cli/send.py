import click

from brother_label_printer_control_ql.backends import Backend

@click.command(name="send", short_help="send an instruction file to the printer")
@click.argument("instructions", type=click.File("rb"))
@click.pass_context
def send_cmd(ctx, *args, **kwargs):
    backend = Backend(ctx.meta.get("BACKEND"))
    printer = backend.printer(ctx.meta.get("PRINTER"))
    printer.send(instructions=kwargs["instructions"].read(), blocking=True)
