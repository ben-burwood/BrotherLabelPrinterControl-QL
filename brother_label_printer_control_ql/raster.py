"""
This module contains the implementation of the raster language
of the Brother QL-series label printers according to their
documentation and to reverse engineering efforts.

The central piece of code in this module is the class
:py:class:`BrotherQLRaster`.
"""

import logging
from typing import Type

import PIL.ImageChops
import PIL.ImageOps
from PIL import Image

from brother_label_printer_control_ql.labels.label_options import LabelOptions
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
    right_margin_addition,
    two_color_support,
)
from .exceptions import BrotherQLError, BrotherQLRasterError, BrotherQLUnknownModel, BrotherQLUnsupportedCmd
from .instructions import (
    add_autocut,
    add_compression,
    add_cut_every,
    add_expanded_mode,
    add_initialize,
    add_invalidate,
    add_margins,
    add_media_and_quality,
    add_print,
    add_raster_data,
    add_status_information,
    add_switch_mode,
)
from .utils.image_trafos import filtered_hsv
from .utils.pixels import get_pixel_width

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

    def add_initialize(self, data: bytes) -> bytes:
        self.page_number = 0
        return add_initialize(data)

    def add_switch_mode(self, data: bytes) -> bytes:
        """
        Switch dynamic command mode
        Switch to the raster mode on the printers that support
        the mode change (others are in raster mode already).
        """
        if self.model not in modesetting:
            self._unsupported("Trying to switch the operating mode on a printer that doesn't support the command.")
            return data
        return add_switch_mode(data)

    def add_media_and_quality(self, data: bytes, rnumber: int) -> bytes:
        return add_media_and_quality(data, rnumber, self._pquality, self.mtype, self.mwidth, self.mlength, self.page_number)

    def add_autocut(self, data: bytes, autocut: bool = False) -> bytes:
        if self.model not in cuttingsupport:
            self._unsupported("Trying to call add_autocut with a printer that doesn't support it")
            return data

        return add_autocut(data, autocut)

    def add_cut_every(self, data: bytes, n: int = 1) -> bytes:
        if self.model not in cuttingsupport:
            self._unsupported("Trying to call add_cut_every with a printer that doesn't support it")
            return data

        return add_cut_every(data, n)

    def add_expanded_mode(self, data: bytes) -> bytes:
        if self.model not in expandedmode:
            self._unsupported("Trying to set expanded mode (dpi/cutting at end) on a printer that doesn't support it")
            return data

        if self.two_color_printing and not self.two_color_support:
            self._unsupported("Trying to set two_color_printing in expanded mode on a printer that doesn't support it.")
            return data

        return add_expanded_mode(data, self.cut_at_end, self.dpi_600, self.two_color_printing)

    def add_compression(self, data: bytes, compression: bool = True) -> bytes:
        """
        Add an instruction enabling or disabling compression for the transmitted raster image lines.
        Not all models support compression. If the specific model doesn't support it but this method
        is called trying to enable it, either a warning is set or an exception is raised depending on
        the value of :py:attr:`exception_on_warning`

        :param bool compression: Whether compression should be on or off
        """
        if self.model not in compressionsupport:
            self._unsupported("Trying to set compression on a printer that doesn't support it")
            return data

        self._compression = compression
        return add_compression(data, compression)

    def add_raster_data(self, data: bytes, image: Image, second_image: Image = None) -> bytes:
        """
        Add the image data to the instructions.
        The provided image has to be binary (every pixel
        is either black or white).

        :param PIL.Image.Image image: The image to be converted and added to the raster instructions
        :param PIL.Image.Image second_image: A second image with a separate color layer (red layer for the QL-800 series)
        """
        logger.debug("raster_image_size: {0}x{1}".format(*image.size))
        return add_raster_data(data, self.model, self._compression, image, second_image)

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
        device_pixel_width = get_pixel_width(self.model)

        label_options = LabelOptions.from_dict(kwargs)

        if label_options.red and not self.two_color_support:
            raise BrotherQLUnsupportedCmd("Printing in red is not supported with the selected model.")

        try:
            self.data = self.add_switch_mode(self.data)
        except BrotherQLUnsupportedCmd:
            pass

        self.data = add_invalidate(self.data)
        self.data = self.add_initialize(self.data)

        try:
            self.data = self.add_switch_mode(self.data)
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
                im = im.convert("RGB" if label_options.red else "L")
            elif im.mode == "L" and label_options.red:
                # Convert greyscale to RGB if printing on black/red tape
                im = im.convert("RGB")

            if label_options.dpi_600:
                dots_expected = [el * 2 for el in dots_printable]
            else:
                dots_expected = dots_printable

            if label_specs["kind"] in (ENDLESS_LABEL, PTOUCH_ENDLESS_LABEL):
                if label_options.rotate not in ("auto", 0):
                    im = im.rotate(label_options.rotate, expand=True)
                if label_options.dpi_600:
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
                if label_options.rotate == "auto":
                    if im.size[0] == dots_expected[1] and im.size[1] == dots_expected[0]:
                        im = im.rotate(90, expand=True)
                elif label_options.rotate != 0:
                    im = im.rotate(label_options.rotate, expand=True)
                if im.size[0] != dots_expected[0] or im.size[1] != dots_expected[1]:
                    raise ValueError("Bad image dimensions: %s. Expecting: %s." % (im.size, dots_expected))
                if label_options.dpi_600:
                    im = im.resize((im.size[0] // 2, im.size[1]))
                new_im = Image.new(im.mode, (device_pixel_width, dots_expected[1]), (255,) * len(im.mode))
                new_im.paste(im, (device_pixel_width - im.size[0] - right_margin_dots, 0))
                im = new_im

            if label_options.red:
                filter_h = lambda h: 255 if (h < 40 or h > 210) else 0
                filter_s = lambda s: 255 if s > 100 else 0
                filter_v = lambda v: 255 if v > 80 else 0
                red_im = filtered_hsv(im, filter_h, filter_s, filter_v)
                red_im = red_im.convert("L")
                red_im = PIL.ImageOps.invert(red_im)
                red_im = red_im.point(lambda x: 0 if x < label_options.threshold else 255, mode="1")

                filter_h = lambda h: 255
                filter_s = lambda s: 255
                filter_v = lambda v: 255 if v < 80 else 0
                black_im = filtered_hsv(im, filter_h, filter_s, filter_v)
                black_im = black_im.convert("L")
                black_im = PIL.ImageOps.invert(black_im)
                black_im = black_im.point(lambda x: 0 if x < label_options.threshold else 255, mode="1")
                black_im = PIL.ImageChops.subtract(black_im, red_im)
            else:
                im = im.convert("L")
                im = PIL.ImageOps.invert(im)

                if label_options.dither:
                    im = im.convert("1", dither=Image.FLOYDSTEINBERG)
                else:
                    im = im.point(lambda x: 0 if x < label_options.threshold else 255, mode="1")

            self.data = add_status_information(self.data)
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
            self.pquality = int(label_options.hq)
            self.data = self.add_media_and_quality(self.data, im.size[1])
            try:
                if label_options.cut:
                    self.data = self.add_autocut(self.data, True)
                    self.data = self.add_cut_every(self.data, 1)
            except BrotherQLUnsupportedCmd:
                pass
            try:
                self.dpi_600 = label_options.dpi_600
                self.cut_at_end = label_options.cut
                self.two_color_printing = True if label_options.red else False
                self.data = self.add_expanded_mode(self.data)
            except BrotherQLUnsupportedCmd:
                pass
            self.data = add_margins(self.data, label_specs["feed_margin"])
            try:
                if label_options.compress:
                    self.data = self.add_compression(self.data, True)
            except BrotherQLUnsupportedCmd:
                pass
            if label_options.red:
                self.data = self.add_raster_data(self.data, black_im, red_im)
            else:
                self.data = self.add_raster_data(self.data, im)
            self.data = add_print(self.data)

        return self.data
