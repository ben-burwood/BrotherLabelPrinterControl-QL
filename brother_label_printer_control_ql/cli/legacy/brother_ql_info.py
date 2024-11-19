import argparse

from brother_label_printer_control_ql.labels import FormFactor, Labels
from brother_label_printer_control_ql.models import Models

def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="action")
    subparser.add_parser("list-label-sizes", help="List available label sizes")
    subparser.add_parser("list-models", help="List available models")
    args = parser.parse_args()

    if not args.action:
        parser.error("Please choose an action")

    elif args.action == "list-models":
        print("Supported models:")
        for model in Models.identifiers():
            print(" " + model)

    elif args.action == "list-label-sizes":
        print("Supported label sizes:")
        fmt = " {label_size:9s} {dots_printable:14s} {label_descr:26s}"
        print(fmt.format(label_size="Name", label_descr="Description", dots_printable="Printable px"))
        for label in Labels:
            label = label.value
            if label.form_factor == FormFactor.DIE_CUT:
                label_descr = "(%d x %d mm^2)" % label.tape_size
                dots_printable = "{0:4d} x {1:4d}".format(*label.dots_printable)
            if label.form_factor == FormFactor.ENDLESS:
                label_descr = "(%d mm endless)" % label.tape_size[0]
                dots_printable = "{0:4d}".format(*label.dots_printable)
            if label.form_factor == FormFactor.ROUND_DIE_CUT:
                label_descr = "(%d mm diameter, round)" % label.tape_size[0]
                dots_printable = "{0:4d} x {1:4d}".format(*label.dots_printable)
            print(fmt.format(label_size=label.identifier, label_descr=label_descr, dots_printable=dots_printable))


if __name__ == "__main__":
    main()
