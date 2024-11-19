from ..devicedependent import number_bytes_per_row


def get_pixel_width(model: str) -> int:
    try:
        nbpr = number_bytes_per_row[model]
    except KeyError:
        nbpr = number_bytes_per_row["default"]
    return nbpr * 8
