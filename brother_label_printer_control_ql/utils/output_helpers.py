import logging

from ..labels import FormFactor, Label

logger = logging.getLogger(__name__)


def textual_label_description(labels_to_include: list[Label]) -> str:
    output = "Supported label sizes:\n"
    output += ""
    fmt = " {label_size:9s} {dots_printable:14s} {label_descr:26s}\n"
    output += fmt.format(label_size="Name", dots_printable="Printable px", label_descr="Description")
    # output += fmt.format(label_size="", dots_printable="width x height", label_descr="")
    for label in labels_to_include:
        if label.form_factor in (FormFactor.DIE_CUT, FormFactor.ROUND_DIE_CUT):
            dp_fmt = "{0:4d} x {1:4d}"
        elif label.form_factor == FormFactor.ENDLESS:
            dp_fmt = "{0:4d}"
        else:
            dp_fmt = " - unknown - "
        dots_printable = dp_fmt.format(*label.dots_printable)
        label_descr = label.identifier
        output += fmt.format(label_size=label.identifier, dots_printable=dots_printable, label_descr=label_descr)
    return output


def log_discovered_devices(available_devices: list[str], level=logging.INFO) -> None:
    for ad in available_devices:
        result = {"model": "unknown", "identifier": ad}
        logger.log(level, "  Found a label printer: {identifier}  (model: {model})".format(**result))
