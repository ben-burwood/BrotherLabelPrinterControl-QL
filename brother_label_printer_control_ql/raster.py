"""
This module contains the implementation of the raster language
of the Brother QL-series label printers according to their
documentation and to reverse engineering efforts.

The central piece of code in this module is the class
:py:class:`BrotherQLRaster`.
"""

import logging
import struct
from io import BytesIO
from typing import Type

import PIL.ImageChops
import PIL.ImageOps
import packbits
from PIL import Image

from .devicedependent import (
    DIE_CUT_LABEL,
    ENDLESS_LABEL,
    PTOUCH_ENDLESS_LABEL,
    ROUND_DIE_CUT_LABEL,
    compressionsupport,
    cuttingsupport,
    expandedmode,
    label_type_specs,
    models,
    modesetting,
    number_bytes_per_row,
    right_margin_addition,
    two_color_support,
)
from .exceptions import BrotherQLError, BrotherQLRasterError, BrotherQLUnknownModel, BrotherQLUnsupportedCmd
from .utils.image_trafos import filtered_hsv

logger = logging.getLogger(__name__)


class BrotherQLRaster:
    """
    This class facilitates the creation of a complete set of raster instructions by adding them one after the other
    using the methods of the class. Each method call is adding instructions to the member variable :py:attr:`data`.

    Instantiate the class by providing the printer model as argument.

    :param str model: Choose from the list of available models.

    :ivar bytes data: The resulting bytecode with all instructions.
    :ivar bool exception_on_warning: If set to True, an exception is raised if trying to add instruction which are not supported on the selected model. If set to False, the instruction is simply ignored and a warning sent to logging/stderr.
    """

    def __init__(self, model: str = "QL-500") -> None:
        if model not in models:
            raise BrotherQLUnknownModel()

        self.model = model
        self.data = b""
        self._pquality = True
        self.page_number = 0
        self.cut_at_end = True
        self.dpi_600 = False
        self.two_color_printing = False
        self._compression = False
        self.exception_on_warning = False

    @property
    def mtype(self) -> bytes:
        return self._mtype

    @property
    def mwidth(self) -> bytes:
        return self._mwidth

    @property
    def mlength(self) -> bytes:
        return self._mlength

    @property
    def pquality(self) -> bool:
        return self._pquality

    @mtype.setter
    def mtype(self, value) -> None:
        self._mtype = bytes([value & 0xFF])

    @mwidth.setter
    def mwidth(self, value) -> None:
        self._mwidth = bytes([value & 0xFF])

    @mlength.setter
    def mlength(self, value) -> None:
        self._mlength = bytes([value & 0xFF])

    @pquality.setter
    def pquality(self, value) -> None:
        self._pquality = bool(value)

    def _warn(self, problem: str, kind: Type[BrotherQLError] = BrotherQLRasterError) -> None:
        """
        Logs the warning message `problem` or raises a
        `BrotherQLRasterError` exception (changeable via `kind`)
        if `self.exception_on_warning` is set to True.

        :raises BrotherQLRasterError: Or other exception \
            set via the `kind` keyword argument.
        """
        if self.exception_on_warning:
            raise kind(problem)
        else:
            logger.warning(problem)

    def _unsupported(self, problem: str) -> None:
        """
        Raises BrotherQLUnsupportedCmd if
        exception_on_warning is set to True.
        Issues a logger warning otherwise.

        :raises BrotherQLUnsupportedCmd:
        """
        self._warn(problem, kind=BrotherQLUnsupportedCmd)

    @property
    def two_color_support(self) -> bool:
        return self.model in two_color_support

    def add_initialize(self) -> None:
        self.page_number = 0
        self.data += b"\x1B\x40"  # ESC @

    def add_status_information(self) -> None:
        """Status Information Request"""
        self.data += b"\x1B\x69\x53"  # ESC i S

    def add_switch_mode(self) -> None:
        """
        Switch dynamic command mode
        Switch to the raster mode on the printers that support
        the mode change (others are in raster mode already).
        """
        if self.model not in modesetting:
            self._unsupported("Trying to switch the operating mode on a printer that doesn't support the command.")
            return
        self.data += b"\x1B\x69\x61\x01"  # ESC i a

    def add_invalidate(self) -> None:
        """clear command buffer"""
        self.data += b"\x00" * 200

    def add_media_and_quality(self, rnumber: bytes) -> None:
        self.data += b"\x1B\x69\x7A"  # ESC i z
        valid_flags = 0x80
        valid_flags |= (self._mtype is not None) << 1
        valid_flags |= (self._mwidth is not None) << 2
        valid_flags |= (self._mlength is not None) << 3
        valid_flags |= self._pquality << 6
        self.data += bytes([valid_flags])
        vals = [self._mtype, self._mwidth, self._mlength]
        self.data += b"".join(b"\x00" if val is None else val for val in vals)
        self.data += struct.pack("<L", rnumber)
        self.data += bytes([0 if self.page_number == 0 else 1])
        self.data += b"\x00"
        # INFO:  media/quality (1B 69 7A) --> found! (payload: 8E 0A 3E 00 D2 00 00 00 00 00)

    def add_autocut(self, autocut: bool = False) -> None:
        if self.model not in cuttingsupport:
            self._unsupported("Trying to call add_autocut with a printer that doesn't support it")
            return

        self.data += b"\x1B\x69\x4D"  # ESC i M
        self.data += bytes([autocut << 6])

    def add_cut_every(self, n: int = 1) -> None:
        if self.model not in cuttingsupport:
            self._unsupported("Trying to call add_cut_every with a printer that doesn't support it")
            return

        self.data += b"\x1B\x69\x41"  # ESC i A
        self.data += bytes([n & 0xFF])

    def add_expanded_mode(self) -> None:
        if self.model not in expandedmode:
            self._unsupported("Trying to set expanded mode (dpi/cutting at end) on a printer that doesn't support it")
            return

        if self.two_color_printing and not self.two_color_support:
            self._unsupported("Trying to set two_color_printing in expanded mode on a printer that doesn't support it.")
            return

        self.data += b"\x1B\x69\x4B"  # ESC i K
        flags = 0x00
        flags |= self.cut_at_end << 3
        flags |= self.dpi_600 << 6
        flags |= self.two_color_printing << 0
        self.data += bytes([flags])

    def add_margins(self, dots: int = 0x23) -> None:
        self.data += b"\x1B\x69\x64"  # ESC i d
        self.data += struct.pack("<H", dots)

    def add_compression(self, compression: bool = True) -> None:
        """
        Add an instruction enabling or disabling compression for the transmitted raster image lines.
        Not all models support compression. If the specific model doesn't support it but this method
        is called trying to enable it, either a warning is set or an exception is raised depending on
        the value of :py:attr:`exception_on_warning`

        :param bool compression: Whether compression should be on or off
        """
        if self.model not in compressionsupport:
            self._unsupported("Trying to set compression on a printer that doesn't support it")
            return

        self._compression = compression
        self.data += b"\x4D"  # M
        self.data += bytes([compression << 1])

    def get_pixel_width(self) -> int:
        try:
            nbpr = number_bytes_per_row[self.model]
        except KeyError:
            nbpr = number_bytes_per_row["default"]
        return nbpr * 8

    def add_raster_data(self, image: Image, second_image: Image = None) -> None:
        """
        Add the image data to the instructions.
        The provided image has to be binary (every pixel
        is either black or white).

        :param PIL.Image.Image image: The image to be converted and added to the raster instructions
        :param PIL.Image.Image second_image: A second image with a separate color layer (red layer for the QL-800 series)
        """
        logger.debug("raster_image_size: {0}x{1}".format(*image.size))
        if image.size[0] != self.get_pixel_width():
            fmt = "Wrong pixel width: {}, expected {}"
            raise BrotherQLRasterError(fmt.format(image.size[0], self.get_pixel_width()))

        images = [image]
        if second_image:
            if image.size != second_image.size:
                fmt = "First and second image don't have the same dimesions: {} vs {}."
                raise BrotherQLRasterError(fmt.format(image.size, second_image.size))
            images.append(second_image)

        frames = []
        for image in images:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            image = image.convert("1")
            frames.append(bytes(image.tobytes(encoder_name="raw")))

        frame_len = len(frames[0])
        row_len = images[0].size[0] // 8
        start = 0
        file_str = BytesIO()
        while start + row_len <= frame_len:
            for i, frame in enumerate(frames):
                row = frame[start : start + row_len]
                if self._compression:
                    row = packbits.encode(row)
                translen = len(row)  # number of bytes to be transmitted
                if self.model.startswith("PT"):
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
        self.data += file_str.getvalue()

    def add_print(self, last_page: bool = True) -> None:
        if last_page:
            self.data += b"\x1A"  # 0x1A = ^Z = SUB; here: EOF = End of File
        else:
            self.data += b"\x0C"  # 0x0C = FF  = Form Feed

    def generate_instructions(self, images: list[Image | str], label: str, **kwargs):
        """Converts one or more images to a raster instruction file.

        :param qlr:
            An instance of the BrotherQLRaster class
        :type qlr: :py:class:`brother_ql.raster.BrotherQLRaster`
        :param images:
            The images to be converted. They can be filenames or instances of Pillow's Image.
        :type images: list(PIL.Image.Image) or list(str) images
        :param str label:
            Type of label the printout should be on.
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * **cut** (``bool``) --
              Enable cutting after printing the labels.
            * **dither** (``bool``) --
              Instead of applying a threshold to the pixel values, approximate grey tones with dithering.
            * **compress**
            * **red**
            * **rotate**
            * **dpi_600**
            * **hq**
            * **threshold**
        """
        label_specs = label_type_specs[label]

        dots_printable = label_specs["dots_printable"]
        right_margin_dots = label_specs["right_margin_dots"]
        right_margin_dots += right_margin_addition.get(self.model, 0)
        device_pixel_width = self.get_pixel_width()

        cut = kwargs.get("cut", True)

        dither = kwargs.get("dither", False)

        compress = kwargs.get("compress", False)

        red = kwargs.get("red", False)

        rotate = kwargs.get("rotate", "auto")
        rotate = int(rotate) if rotate != "auto" else rotate

        dpi_600 = kwargs.get("dpi_600", False)

        hq = kwargs.get("hq", True)

        threshold = kwargs.get("threshold", 70)
        threshold = 100.0 - threshold
        threshold = min(255, max(0, int(threshold / 100.0 * 255)))

        if red and not self.two_color_support:
            raise BrotherQLUnsupportedCmd("Printing in red is not supported with the selected model.")

        try:
            self.add_switch_mode()
        except BrotherQLUnsupportedCmd:
            pass

        self.add_invalidate()
        self.add_initialize()

        try:
            self.add_switch_mode()
        except BrotherQLUnsupportedCmd:
            pass

        for image in images:
            if isinstance(image, Image.Image):
                im = image
            else:
                try:
                    im = Image.open(image)
                except:
                    raise NotImplementedError("The image argument needs to be an Image() instance, the filename to an image, or a file handle.")

            if im.mode.endswith("A"):
                # place in front of white background and get red of transparency
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, im.split()[-1])
                im = bg
            elif im.mode == "P":
                # Convert GIF ("P") to RGB
                im = im.convert("RGB" if red else "L")
            elif im.mode == "L" and red:
                # Convert greyscale to RGB if printing on black/red tape
                im = im.convert("RGB")

            if dpi_600:
                dots_expected = [el * 2 for el in dots_printable]
            else:
                dots_expected = dots_printable

            if label_specs["kind"] in (ENDLESS_LABEL, PTOUCH_ENDLESS_LABEL):
                if rotate not in ("auto", 0):
                    im = im.rotate(rotate, expand=True)
                if dpi_600:
                    im = im.resize((im.size[0] // 2, im.size[1]))
                if im.size[0] != dots_printable[0]:
                    hsize = int((dots_printable[0] / im.size[0]) * im.size[1])
                    im = im.resize((dots_printable[0], hsize), Image.Resampling.LANCZOS)
                    logger.warning("Need to resize the image...")
                if im.size[0] < device_pixel_width:
                    new_im = Image.new(im.mode, (device_pixel_width, im.size[1]), (255,) * len(im.mode))
                    new_im.paste(im, (device_pixel_width - im.size[0] - right_margin_dots, 0))
                    im = new_im
            elif label_specs["kind"] in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
                if rotate == "auto":
                    if im.size[0] == dots_expected[1] and im.size[1] == dots_expected[0]:
                        im = im.rotate(90, expand=True)
                elif rotate != 0:
                    im = im.rotate(rotate, expand=True)
                if im.size[0] != dots_expected[0] or im.size[1] != dots_expected[1]:
                    raise ValueError("Bad image dimensions: %s. Expecting: %s." % (im.size, dots_expected))
                if dpi_600:
                    im = im.resize((im.size[0] // 2, im.size[1]))
                new_im = Image.new(im.mode, (device_pixel_width, dots_expected[1]), (255,) * len(im.mode))
                new_im.paste(im, (device_pixel_width - im.size[0] - right_margin_dots, 0))
                im = new_im

            if red:
                filter_h = lambda h: 255 if (h < 40 or h > 210) else 0
                filter_s = lambda s: 255 if s > 100 else 0
                filter_v = lambda v: 255 if v > 80 else 0
                red_im = filtered_hsv(im, filter_h, filter_s, filter_v)
                red_im = red_im.convert("L")
                red_im = PIL.ImageOps.invert(red_im)
                red_im = red_im.point(lambda x: 0 if x < threshold else 255, mode="1")

                filter_h = lambda h: 255
                filter_s = lambda s: 255
                filter_v = lambda v: 255 if v < 80 else 0
                black_im = filtered_hsv(im, filter_h, filter_s, filter_v)
                black_im = black_im.convert("L")
                black_im = PIL.ImageOps.invert(black_im)
                black_im = black_im.point(lambda x: 0 if x < threshold else 255, mode="1")
                black_im = PIL.ImageChops.subtract(black_im, red_im)
            else:
                im = im.convert("L")
                im = PIL.ImageOps.invert(im)

                if dither:
                    im = im.convert("1", dither=Image.FLOYDSTEINBERG)
                else:
                    im = im.point(lambda x: 0 if x < threshold else 255, mode="1")

            self.add_status_information()
            tape_size = label_specs["tape_size"]
            if label_specs["kind"] in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
                self.mtype = 0x0B
                self.mwidth = tape_size[0]
                self.mlength = tape_size[1]
            elif label_specs["kind"] in (ENDLESS_LABEL,):
                self.mtype = 0x0A
                self.mwidth = tape_size[0]
                self.mlength = 0
            elif label_specs["kind"] in (PTOUCH_ENDLESS_LABEL,):
                self.mtype = 0x00
                self.mwidth = tape_size[0]
                self.mlength = 0
            self.pquality = int(hq)
            self.add_media_and_quality(im.size[1])
            try:
                if cut:
                    self.add_autocut(True)
                    self.add_cut_every(1)
            except BrotherQLUnsupportedCmd:
                pass
            try:
                self.dpi_600 = dpi_600
                self.cut_at_end = cut
                self.two_color_printing = True if red else False
                self.add_expanded_mode()
            except BrotherQLUnsupportedCmd:
                pass
            self.add_margins(label_specs["feed_margin"])
            try:
                if compress:
                    self.add_compression(True)
            except BrotherQLUnsupportedCmd:
                pass
            if red:
                self.add_raster_data(black_im, red_im)
            else:
                self.add_raster_data(im)
            self.add_print()

        return self.data
