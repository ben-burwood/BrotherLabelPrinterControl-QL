from dataclasses import dataclass, field
from enum import Enum

from .color import Color
from .form_factor import FormFactor
from ..models import Model, Models

@dataclass(frozen=True)
class Label:
    """
    All specifics of a certain label and what the rasterizer needs to take care of depending on the label chosen, should be contained in this class.
    """

    # A string identifier given to each label that can be selected. Eg. '29'.
    identifier: str
    # The tape size of a single label (width, lenght) in mm. For endless labels, the length is 0 by definition.
    tape_size: tuple[int, int]
    # The type of label
    form_factor: FormFactor
    # The total area (width, length) of the label in dots (@300dpi).
    dots_total: tuple[int, int]
    # The printable area (width, length) of the label in dots (@300dpi).
    dots_printable: tuple[int, int]
    # The required offset from the right side of the label in dots to obtain a centered printout.
    offset_r: int
    # An additional amount of feeding when printing the label.
    # This is non-zero for some smaller label sizes and for endless labels.
    feed_margin: int = 0
    # If a label can only be printed with certain label printers, this member variable lists the allowed ones.
    # Otherwise it's an empty list.
    restricted_to_models: list[Models] = field(default_factory=list)
    # Some labels allow printing in red, most don't.
    color: Color = Color.BLACK_WHITE

    @property
    def name(self) -> str:
        if "x" in self.identifier:
            out = "{0}mm x {1}mm die-cut".format(*self.tape_size)
        elif self.identifier.startswith("d"):
            out = "{0}mm round die-cut".format(self.tape_size[0])
        else:
            out = "{0}mm endless".format(self.tape_size[0])

        if self.color == Color.BLACK_RED_WHITE:
            out += " (black/red/white)"

        return out

    def works_with_model(self, model: Model) -> bool:
        """Method to determine if certain label can be printed by the specified printer model."""
        if not self.restricted_to_models:
            return False

        for restricted_model in self.restricted_to_models:
            if model == restricted_model.value:
                return True

        return False


class Labels(Enum):
    L12 = Label("12", (12, 0), FormFactor.ENDLESS, (142, 0), (106, 0), 29, feed_margin=35)
    L29 = Label("29", (29, 0), FormFactor.ENDLESS, (342, 0), (306, 0), 6, feed_margin=35)
    L38 = Label("38", (38, 0), FormFactor.ENDLESS, (449, 0), (413, 0), 12, feed_margin=35)
    L50 = Label("50", (50, 0), FormFactor.ENDLESS, (590, 0), (554, 0), 12, feed_margin=35)
    L54 = Label("54", (54, 0), FormFactor.ENDLESS, (636, 0), (590, 0), 0, feed_margin=35)
    L62 = Label("62", (62, 0), FormFactor.ENDLESS, (732, 0), (696, 0), 12, feed_margin=35)
    L62RED = Label("62red", (62, 0), FormFactor.ENDLESS, (732, 0), (696, 0), 12, feed_margin=35, color=Color.BLACK_RED_WHITE)
    L102 = Label("102", (102, 0), FormFactor.ENDLESS, (1200, 0), (1164, 0), 12, feed_margin=35, restricted_to_models=[Models.QL1050, Models.QL1060N])
    L17X54 = Label("17x54", (17, 54), FormFactor.DIE_CUT, (201, 636), (165, 566), 0)
    L17X87 = Label("17x87", (17, 87), FormFactor.DIE_CUT, (201, 1026), (165, 956), 0)
    L23X23 = Label("23x23", (23, 23), FormFactor.DIE_CUT, (272, 272), (202, 202), 42)
    L29X42 = Label("29x42", (29, 42), FormFactor.DIE_CUT, (342, 495), (306, 425), 6)
    L29X90 = Label("29x90", (29, 90), FormFactor.DIE_CUT, (342, 1061), (306, 991), 6)
    L39X90 = Label("39x90", (38, 90), FormFactor.DIE_CUT, (449, 1061), (413, 991), 12)
    L39X48 = Label("39x48", (39, 48), FormFactor.DIE_CUT, (461, 565), (425, 495), 6)
    L52X29 = Label("52x29", (52, 29), FormFactor.DIE_CUT, (614, 341), (578, 271), 0)
    L62X29 = Label("62x29", (62, 29), FormFactor.DIE_CUT, (732, 341), (696, 271), 12)
    L62X100 = Label("62x100", (62, 100), FormFactor.DIE_CUT, (732, 1179), (696, 1109), 12)
    L102X51 = Label("102x51", (102, 51), FormFactor.DIE_CUT, (1200, 596), (1164, 526), 12, restricted_to_models=[Models.QL1050, Models.QL1060N])
    L102X152 = Label("102x152", (102, 153), FormFactor.DIE_CUT, (1200, 1804), (1164, 1660), 12, restricted_to_models=[Models.QL1050, Models.QL1060N])
    LD12 = Label("d12", (12, 12), FormFactor.ROUND_DIE_CUT, (142, 142), (94, 94), 113, feed_margin=35)
    LD24 = Label("d24", (24, 24), FormFactor.ROUND_DIE_CUT, (284, 284), (236, 236), 42)
    LD58 = Label("d58", (58, 58), FormFactor.ROUND_DIE_CUT, (688, 688), (618, 618), 51)
    LPT24 = Label("pt24", (24, 0), FormFactor.PTOUCH_ENDLESS, (128, 0), (128, 0), 0, feed_margin=14)

    @staticmethod
    def from_identifier(identifier: str) -> Label:
        for label in Labels:
            if label.value.identifier == identifier:
                return label.value
        else:
            raise ValueError(f"Label with identifier '{identifier}' not found.")

    @staticmethod
    def identifiers() -> list[str]:
        return [label.value.identifier for label in Labels]
