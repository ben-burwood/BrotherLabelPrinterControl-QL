from dataclasses import dataclass


@dataclass(frozen=True)
class OpCode:
    signature: bytes
    name: str
    following_bytes: int
    description: str


OPCODES = [
    OpCode(b"\x00", "preamble", -1, "Preamble, 200-300x 0x00 to clear comamnd buffer"),
    OpCode(b"\x4D", "compression", 1, ""),
    OpCode(b"\x67", "raster QL", -1, ""),
    OpCode(b"\x47", "raster P-touch", -1, ""),
    OpCode(b"\x77", "2-color raster QL", -1, ""),
    OpCode(b"\x5a", "zero raster", 0, "empty raster line"),
    OpCode(b"\x0C", "print", 0, "print intermediate page"),
    OpCode(b"\x1A", "print", 0, "print final page"),
    OpCode(b"\x1b\x40", "init", 0, "initialization"),
    OpCode(b"\x1b\x69\x61", "mode setting", 1, ""),
    OpCode(b"\x1b\x69\x21", "automatic status", 1, ""),
    OpCode(b"\x1b\x69\x7A", "media/quality", 10, "print-media and print-quality"),
    OpCode(b"\x1b\x69\x4D", "various", 1, "Auto cut flag in bit 7"),
    OpCode(b"\x1b\x69\x41", "cut-every", 1, "cut every n-th page"),
    OpCode(b"\x1b\x69\x4B", "expanded", 1, ""),
    OpCode(b"\x1b\x69\x64", "margins", 2, ""),
    OpCode(b"\x1b\x69\x55\x77\x01", "amedia", 127, "Additional media information command"),
    OpCode(b"\x1b\x69\x55\x4A", "jobid", 14, "Job ID setting command"),
    OpCode(b"\x1b\x69\x58\x47", "request_config", 0, "Request transmission of .ini config file of printer"),
    OpCode(b"\x1b\x69\x53", "status request", 0, "A status information request sent to the printer"),
    OpCode(b"\x80\x20\x42", "status response", 29, "A status response received from the printer"),
]


def match_opcode(data: bytes) -> OpCode:
    matching_opcodes = [opcode for opcode in OPCODES if data.startswith(opcode.signature)]
    assert len(matching_opcodes) == 1
    return matching_opcodes[0]
