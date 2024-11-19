import click

from ..backends import Backend
from ..labels import Labels
from ..models import Models
from ..raster import BrotherQLRaster


@click.command("print", short_help="Print a label")
@click.argument("images", nargs=-1, type=click.File("rb"), metavar="IMAGE [IMAGE] ...")
@click.option(
    "-l",
    "--label",
    type=click.Choice(Labels.identifiers()),
    envvar="BROTHER_QL_LABEL",
    help="The label (size, type - die-cut or endless). Run `brother_ql info labels` for a full list including ideal pixel dimensions.",
)
@click.option("-r", "--rotate", type=click.Choice(("auto", "0", "90", "180", "270")), default="auto", help="Rotate the image (counterclock-wise) by this amount of degrees.")
@click.option("-t", "--threshold", type=float, default=70.0, help="The threshold value (in percent) to discriminate between black and white pixels.")
@click.option("-d", "--dither", is_flag=True, help="Enable dithering when converting the image to b/w. If set, --threshold is meaningless.")
@click.option(
    "-c",
    "--compress",
    is_flag=True,
    help="Enable compression (if available with the model). Label creation can take slightly longer but the resulting instruction size is normally considerably smaller.",
)
@click.option(
    "--red",
    is_flag=True,
    help="Create a label to be printed on black/red/white tape (only with QL-8xx series on DK-22251 labels). You must use this option when printing on black/red tape, even when not printing red.",
)
@click.option(
    "--600dpi", "dpi_600", is_flag=True, help="Print with 600x300 dpi available on some models. Provide your image as 600x600 dpi; perpendicular to the feeding the image will be resized to 300dpi."
)
@click.option("--lq", is_flag=True, help="Print with low quality (faster). Default is high quality.")
@click.option("--no-cut", is_flag=True, help="Don't cut the tape after printing the label.")
@click.pass_context
def print_cmd(ctx, *args, **kwargs):
    """Print a label of the provided IMAGE."""
    backend = Backend(ctx.meta.get("BACKEND", "pyusb"))
    model = Models.from_identifier(ctx.meta.get("MODEL"))
    printer_identifier = ctx.meta.get("PRINTER")

    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True

    kwargs["cut"] = not kwargs["no_cut"]
    del kwargs["no_cut"]
    images = kwargs["images"]
    del kwargs["images"]
    label = Labels.from_identifier(kwargs["label"])
    del kwargs["label"]
    instructions = qlr.generate_instructions(images, label, **kwargs)

    printer = backend.printer(printer_identifier)
    printer.send(instructions=instructions, blocking=True)
