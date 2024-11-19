from dataclasses import dataclass
from enum import Enum

from .exceptions import BrotherQLUnknownModel


@dataclass
class Model:
    """
    This class represents a printer model. All specifics of a certain model
    and the opcodes it supports should be contained in this class.
    """

    # A string identifier given to each model implemented. Eg. 'QL-500'.
    identifier: str
    # Minimum and maximum number of rows or 'dots' that can be printed.
    # Together with the dpi this gives the minimum and maximum length
    # for continuous tape printing.
    min_max_length_dots: tuple[int, int]
    # The minimum and maximum amount of feeding a label
    min_max_feed: tuple[int, int] = (35, 1500)
    number_bytes_per_row: int = 90
    # The required additional offset from the right side
    additional_offset_r: int = 0
    # Support for the 'mode setting' opcode
    mode_setting: bool = True
    # Model has a cutting blade to automatically cut labels
    cutting: bool = True
    # Model has support for the 'expanded mode' opcode.
    # (So far, all models that have cutting support do).
    expanded_mode: bool = True
    # Model has support for compressing the transmitted raster data.
    # Some models with only USB connectivity don't support compression.
    compression: bool = True
    # Support for two color printing (black/red/white)
    # available only on some newer models.
    two_color: bool = False

    @property
    def name(self):
        return self.identifier

    @property
    def pixel_width(self) -> int:
        return self.number_bytes_per_row * 8


class Models(Enum):
    QL500 = Model("QL-500", (295, 11811), compression=False, mode_setting=False, expanded_mode=False, cutting=False)
    QL550 = Model("QL-550", (295, 11811), compression=False, mode_setting=False)
    QL560 = Model("QL-560", (295, 11811), compression=False, mode_setting=False)
    QL570 = Model("QL-570", (150, 11811), compression=False, mode_setting=False)
    QL580N = Model("QL-580N", (150, 11811))
    QL650TD = Model("QL-650TD", (295, 11811))
    QL700 = Model("QL-700", (150, 11811), compression=False, mode_setting=False)
    QL710W = Model("QL-710W", (150, 11811))
    QL720NW = Model("QL-720NW", (150, 11811))
    QL800 = Model("QL-800", (150, 11811), two_color=True, compression=False)
    QL810W = Model("QL-810W", (150, 11811), two_color=True)
    QL820NWB = Model("QL-820NWB", (150, 11811), two_color=True)
    QL1050 = Model("QL-1050", (295, 35433), number_bytes_per_row=162, additional_offset_r=44)
    QL1060N = Model("QL-1060N", (295, 35433), number_bytes_per_row=162, additional_offset_r=44)
    PTP750W = Model("PT-P750W", (31, 14172), number_bytes_per_row=16)
    PTP900W = Model("PT-P900W", (57, 28346), number_bytes_per_row=70)

    @staticmethod
    def from_identifier(identifier: str) -> Model:
        try:
            return Models[identifier.upper()].value
        except KeyError:
            raise BrotherQLUnknownModel(f"Model '{identifier}' not implemented.")

    @staticmethod
    def identifiers() -> list[str]:
        return [model.value.identifier for model in Models]
