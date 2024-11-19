from enum import Enum, auto


class PrintOutcome(Enum):
    UNKNOWN = auto()
    SENT = auto()
    PRINTED = auto()
    ERROR = auto()
