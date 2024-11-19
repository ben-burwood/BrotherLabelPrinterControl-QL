from enum import IntEnum


class RespMediaTypes(IntEnum):
    NO_MEDIA = 0x00
    CONTINUOUS_LENGTH_TAPE = 0x0A
    DIE_CUT_LABELS = 0x0B


class RespStatusTypes(IntEnum):
    REPLY_TO_STATUS_REQUEST = 0x00
    PRINTING_COMPLETED = 0x01
    ERROR_OCCURRED = 0x02
    NOTIFICATION = 0x05
    PHASE_CHANGE = 0x06


class RespPhaseTypes(IntEnum):
    WAITING_TO_RECEIVE = 0x00
    PRINTING_STATE = 0x01


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
