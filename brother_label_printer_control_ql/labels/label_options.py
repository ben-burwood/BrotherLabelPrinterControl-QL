from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LabelOptions:
    cut: bool
    dither: bool
    compress: bool
    red: bool
    rotate: int
    dpi_600: bool
    hq: bool
    threshold: int

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "LabelOptions":
        rot = d.get("rotate", "auto")
        rot = int(rot) if rot != "auto" else rot

        thresh = d.get("threshold", 70)
        thresh = 100.0 - thresh
        thresh = min(255, max(0, int(thresh / 100.0 * 255)))

        return LabelOptions(
            cut=d.get("cut", True),
            dither=d.get("dither", False),
            compress=d.get("compress", False),
            red=d.get("red", False),
            rotate=rot,
            dpi_600=d.get("dpi_600", False),
            hq=d.get("hq", True),
            threshold=thresh,
        )
