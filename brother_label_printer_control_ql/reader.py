import io
import logging
import struct

from PIL import Image
from PIL.ImageOps import colorize

from .control.op_codes import OPCODES, match_opcode
from .utils.hex import hex_format

logger = logging.getLogger(__name__)


def chunker(data: bytes, raise_exception: bool = False):
    """
    Breaks data stream (bytes) into a list of bytes objects containing single instructions each.

    Logs warnings for unknown opcodes or raises an exception instead, if raise_exception is set to True.

    returns: list of bytes objects
    """
    instructions = []
    data = bytes(data)
    while True:
        if len(data) == 0:
            break

        try:
            opcode = match_opcode(data)
        except:
            msg = "unknown opcode starting with {}...)".format(hex_format(data[0:4]))
            if raise_exception:
                raise ValueError(msg)
            else:
                logger.warning(msg)
                data = data[1:]
                continue

        num_bytes = len(opcode.signature)
        if opcode.following_bytes > 0:
            num_bytes += opcode.following_bytes
        elif opcode.name in ("raster QL", "2-color raster QL"):
            num_bytes += data[2] + 2
        elif opcode.name in ("raster P-touch",):
            num_bytes += data[1] + data[2] * 256 + 2

        # payload = data[len(opcode):num_bytes]
        instructions.append(data[:num_bytes])

        yield instructions[-1]

        data = data[num_bytes:]
    # return instructions


def merge_specific_instructions(chunks: list, join_preamble: bool = True, join_raster: bool = True) -> list:
    """
    Process a list of instructions by merging subsequent instructions with identical opcodes into "large instructions".
    """
    new_instructions = []
    last_opcode = None
    instruction_buffer = b""
    for instruction in chunks:
        opcode = match_opcode(instruction)
        if join_preamble and opcode.name == "preamble" and last_opcode.name == "preamble":
            instruction_buffer += instruction
        elif join_raster and "raster" in opcode.name and "raster" in last_opcode.name:
            instruction_buffer += instruction
        else:
            if instruction_buffer:
                new_instructions.append(instruction_buffer)
            instruction_buffer = instruction
        last_opcode = opcode
    if instruction_buffer:
        new_instructions.append(instruction_buffer)
    return new_instructions


class BrotherQLReader:
    DEFAULT_FILENAME_FMT = "label{counter:04d}.png"

    def __init__(self, brother_file) -> None:
        if type(brother_file) in (str,):
            brother_file = io.open(brother_file, "rb")
        self.brother_file = brother_file
        self.mwidth, self.mheight = None, None
        self.raster_no = None
        self.black_rows = []
        self.red_rows = []
        self.compression = False
        self.page_counter = 1
        self.two_color_printing = False
        self.cut_at_end = False
        self.high_resolution_printing = False
        self.filename_fmt = self.DEFAULT_FILENAME_FMT

    def analyse(self) -> None:
        instructions = self.brother_file.read()
        for instruction in chunker(instructions):
            for opcode in OPCODES:
                if instruction.startswith(opcode.signature):
                    if opcode.name == "init":
                        self.mwidth, self.mheight = None, None
                        self.raster_no = None
                        self.black_rows = []
                        self.red_rows = []
                    payload = instruction[len(opcode) :]
                    logger.info(" {} ({}) --> found! (payload: {})".format(opcode.name, hex_format(opcode), hex_format(payload)))
                    if opcode.name == "compression":
                        self.compression = payload[0] == 0x02
                    if opcode.name == "zero raster":
                        self.black_rows.append(bytes())
                        if self.two_color_printing:
                            self.red_rows.append(bytes())
                    if opcode.name in ("raster QL", "2-color raster QL", "raster P-touch"):
                        rpl = bytes(payload[2:])  # raster payload
                        if self.compression:
                            row = bytes()
                            index = 0
                            while True:
                                num = rpl[index]
                                if num & 0x80:
                                    num = num - 0x100
                                if num < 0:
                                    num = -num + 1
                                    row += bytes([rpl[index + 1]] * num)
                                    index += 2
                                else:
                                    num = num + 1
                                    row += rpl[index + 1 : index + 1 + num]
                                    index += 1 + num
                                if index >= len(rpl):
                                    break
                        else:
                            row = rpl
                        if opcode.name in ("raster QL", "raster P-touch"):
                            self.black_rows.append(row)
                        else:  # 2-color
                            if payload[0] == 0x01:
                                self.black_rows.append(row)
                            elif payload[0] == 0x02:
                                self.red_rows.append(row)
                            else:
                                raise NotImplementedError("color: 0x%x" % payload[0])
                    if opcode.name == "expanded":
                        self.two_color_printing = bool(payload[0] & (1 << 0))
                        self.cut_at_end = bool(payload[0] & (1 << 3))
                        self.high_resolution_printing = bool(payload[0] & (1 << 6))
                    if opcode.name == "media/quality":
                        self.raster_no = struct.unpack("<L", payload[4:8])[0]
                        self.mwidth = instruction[len(opcode) + 2]
                        self.mlength = instruction[len(opcode) + 3] * 256
                        fmt = " media width: {} mm, media length: {} mm, raster no: {} rows"
                        logger.info(fmt.format(self.mwidth, self.mlength, self.raster_no))
                    if opcode.name == "print":
                        logger.info("Len of black rows: %d", len(self.black_rows))
                        logger.info("Len of red   rows: %d", len(self.red_rows))

                        def get_im(rows):
                            if not len(rows):
                                return None
                            width_dots = max(len(row) for row in rows)
                            height_dots = len(rows)
                            size = (width_dots * 8, height_dots)
                            expanded_rows = []
                            for row in rows:
                                if len(row) == 0:
                                    expanded_rows.append(b"\x00" * width_dots)
                                else:
                                    expanded_rows.append(row)
                            data = bytes(b"".join(expanded_rows))
                            data = bytes([2**8 + ~byte for byte in data])  # invert b/w
                            im = Image.frombytes("1", size, data, decoder_name="raw")
                            return im

                        if not self.two_color_printing:
                            im_black = get_im(self.black_rows)
                            im = im_black
                        else:
                            im_black, im_red = (get_im(rows) for rows in (self.black_rows, self.red_rows))
                            im_black = im_black.convert("RGBA")
                            im_red = im_red.convert("L")
                            im_red = colorize(im_red, (255, 0, 0), (255, 255, 255))
                            im_red = im_red.convert("RGBA")
                            pixdata_black = im_black.load()
                            width, height = im_black.size
                            for y in range(height):
                                for x in range(width):
                                    # replace "white" with "transparent"
                                    if pixdata_black[x, y] == (255, 255, 255, 255):
                                        pixdata_black[x, y] = (255, 255, 255, 0)
                            im_red.paste(im_black, (0, 0), im_black)
                            im = im_red
                        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                        img_name = self.filename_fmt.format(counter=self.page_counter)
                        im.save(img_name)
                        print("Page saved as {}".format(img_name))
                        self.page_counter += 1
