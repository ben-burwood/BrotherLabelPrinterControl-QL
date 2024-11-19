import click

from brother_label_printer_control_ql.reader import BrotherQLReader

@click.command(name="analyze", help="interpret a binary file containing raster instructions for the Brother QL-Series printers")
@click.argument("instructions", type=click.File("rb"))
@click.option("-f", "--filename-format", help="Filename format string. Default is: label{counter:04d}.png.")
@click.pass_context
def analyze_cmd(ctx, *args, **kwargs):
    br = BrotherQLReader(kwargs.get("instructions"))
    if kwargs.get("filename_format"):
        br.filename_fmt = kwargs.get("filename_format")
    br.analyse()
