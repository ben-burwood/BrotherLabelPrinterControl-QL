OPCODES = {
    # signature              name    following bytes   description
    b"\x00": ("preamble", -1, "Preamble, 200-300x 0x00 to clear comamnd buffer"),
    b"\x4D": ("compression", 1, ""),
    b"\x67": ("raster QL", -1, ""),
    b"\x47": ("raster P-touch", -1, ""),
    b"\x77": ("2-color raster QL", -1, ""),
    b"\x5a": ("zero raster", 0, "empty raster line"),
    b"\x0C": ("print", 0, "print intermediate page"),
    b"\x1A": ("print", 0, "print final page"),
    b"\x1b\x40": ("init", 0, "initialization"),
    b"\x1b\x69\x61": ("mode setting", 1, ""),
    b"\x1b\x69\x21": ("automatic status", 1, ""),
    b"\x1b\x69\x7A": ("media/quality", 10, "print-media and print-quality"),
    b"\x1b\x69\x4D": ("various", 1, "Auto cut flag in bit 7"),
    b"\x1b\x69\x41": ("cut-every", 1, "cut every n-th page"),
    b"\x1b\x69\x4B": ("expanded", 1, ""),
    b"\x1b\x69\x64": ("margins", 2, ""),
    b"\x1b\x69\x55\x77\x01": ("amedia", 127, "Additional media information command"),
    b"\x1b\x69\x55\x4A": ("jobid", 14, "Job ID setting command"),
    b"\x1b\x69\x58\x47": ("request_config", 0, "Request transmission of .ini config file of printer"),
    b"\x1b\x69\x53": ("status request", 0, "A status information request sent to the printer"),
    b"\x80\x20\x42": ("status response", 29, "A status response received from the printer"),
}

dot_widths = {
    62: 90 * 8,
}

RESP_ERROR_INFORMATION_1_DEF = {
    0: "No media when printing",
    1: "End of media (die-cut size only)",
    2: "Tape cutter jam",
    3: "Not used",
    4: "Main unit in use (QL-560/650TD/1050)",
    5: "Printer turned off",
    6: "High-voltage adapter (not used)",
    7: "Fan doesn't work (QL-1050/1060N)",
}

RESP_ERROR_INFORMATION_2_DEF = {
    0: "Replace media error",
    1: "Expansion buffer full error",
    2: "Transmission / Communication error",
    3: "Communication buffer full error (not used)",
    4: "Cover opened while printing (Except QL-500)",
    5: "Cancel key (not used)",
    6: "Media cannot be fed (also when the media end is detected)",
    7: "System error",
}

RESP_MEDIA_TYPES = {
    0x00: "No media",
    0x0A: "Continuous length tape",
    0x0B: "Die-cut labels",
}

RESP_STATUS_TYPES = {
    0x00: "Reply to status request",
    0x01: "Printing completed",
    0x02: "Error occurred",
    0x05: "Notification",
    0x06: "Phase change",
}

RESP_PHASE_TYPES = {
    0x00: "Waiting to receive",
    0x01: "Printing state",
}

RESP_BYTE_NAMES = [
    "Print head mark",
    "Size",
    "Fixed (B=0x42)",
    "Device dependent",
    "Device dependent",
    "Fixed (0=0x30)",
    "Fixed (0x00 or 0=0x30)",
    "Fixed (0x00)",
    "Error information 1",
    "Error information 2",
    "Media width",
    "Media type",
    "Fixed (0x00)",
    "Fixed (0x00)",
    "Reserved",
    "Mode",
    "Fixed (0x00)",
    "Media length",
    "Status type",
    "Phase type",
    "Phase number (high)",
    "Phase number (low)",
    "Notification number",
    "Reserved",
    "Reserved",
]
