import struct
from io import BytesIO

import packbits
from PIL import Image

from .exceptions import BrotherQLRasterError
from .models import Model

def add_initialize(data: bytes) -> bytes:
    data += b"\x1B\x40"  # ESC @
    return data


def add_status_information(data: bytes) -> bytes:
    """Status Information Request"""
    data += b"\x1B\x69\x53"  # ESC i S
    return data


def add_invalidate(data: bytes) -> bytes:
    """clear command buffer"""
    data += b"\x00" * 200
    return data


def add_margins(data: bytes, dots: int = 0x23) -> bytes:
    data += b"\x1B\x69\x64"  # ESC i d
    data += struct.pack("<H", dots)
    return data


def add_print(data: bytes, last_page: bool = True) -> bytes:
    if last_page:
        data += b"\x1A"  # 0x1A = ^Z = SUB; here: EOF = End of File
    else:
        data += b"\x0C"  # 0x0C = FF  = Form Feed
    return data


def add_switch_mode(data: bytes) -> bytes:
    """
    Switch dynamic command mode
    Switch to the raster mode on the printers that support
    the mode change (others are in raster mode already).
    """
    data += b"\x1B\x69\x61\x01"  # ESC i a
    return data


def add_media_and_quality(data: bytes, rnumber: int, pquality: int, mtype: bytes, mwidth: bytes, mlength: bytes, page_number: int) -> bytes:
    data += b"\x1B\x69\x7A"  # ESC i z

    valid_flags = 0x80
    valid_flags |= (mtype is not None) << 1
    valid_flags |= (mwidth is not None) << 2
    valid_flags |= (mlength is not None) << 3
    valid_flags |= pquality << 6

    data += bytes([valid_flags])
    vals = [mtype, mwidth, mlength]
    data += b"".join(b"\x00" if val is None else val for val in vals)
    data += struct.pack("<L", rnumber)
    data += bytes([0 if page_number == 0 else 1])
    data += b"\x00"
    # INFO:  media/quality (1B 69 7A) --> found! (payload: 8E 0A 3E 00 D2 00 00 00 00 00)
    return data


def add_autocut(data: bytes, autocut: bool) -> bytes:
    """Autocut"""
    data += b"\x1B\x69\x4D"  # ESC i M
    data += bytes([autocut << 6])
    return data


def add_cut_every(data: bytes, n: int) -> bytes:
    data += b"\x1B\x69\x41"  # ESC i A
    data += bytes([n & 0xFF])
    return data


def add_expanded_mode(data: bytes, cut_at_end: bool, dpi_600: bool, two_color_printing: bool) -> bytes:
    """Expanded Mode"""
    data += b"\x1B\x69\x4B"  # ESC i K

    flags = 0x00
    flags |= cut_at_end << 3
    flags |= dpi_600 << 6
    flags |= two_color_printing << 0

    data += bytes([flags])
    return data


def add_compression(data: bytes, compression: bool) -> bytes:
    """Compression"""
    data += b"\x4D"  # M
    data += bytes([compression << 1])
    return data


def add_raster_data(data: bytes, model: Model, compression: bool, image: Image, second_image: Image = None) -> bytes:
    if image.size[0] != model.pixel_width:
        fmt = "Wrong pixel width: {}, expected {}"
        raise BrotherQLRasterError(fmt.format(image.size[0], model.pixel_width))

    images = [image]
    if second_image:
        if image.size != second_image.size:
            fmt = "First and second image don't have the same dimesions: {} vs {}."
            raise BrotherQLRasterError(fmt.format(image.size, second_image.size))
        images.append(second_image)

    frames = []
    for image in images:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        image = image.convert("1")
        frames.append(bytes(image.tobytes(encoder_name="raw")))

    frame_len = len(frames[0])
    row_len = images[0].size[0] // 8
    start = 0
    file_str = BytesIO()
    while start + row_len <= frame_len:
        for i, frame in enumerate(frames):
            row = frame[start : start + row_len]
            if compression:
                row = packbits.encode(row)
            translen = len(row)  # number of bytes to be transmitted
            if model.identifier.startswith("PT"):
                file_str.write(b"\x47")
                file_str.write(bytes([translen % 256, translen // 256]))
            else:
                if second_image:
                    file_str.write(b"\x77\x01" if i == 0 else b"\x77\x02")
                else:
                    file_str.write(b"\x67\x00")
                file_str.write(bytes([translen]))
            file_str.write(row)
        start += row_len

    data += file_str.getvalue()
    return data
