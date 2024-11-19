def hex_format_byte(byte: bytes) -> str:
    try:
        return "{:02X}".format(byte)
    except ValueError:
        return "{:02X}".format(ord(byte))


def hex_format(data) -> str:
    return " ".join(hex_format_byte(byte) for byte in data)
