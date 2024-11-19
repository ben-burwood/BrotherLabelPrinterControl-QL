from enum import Enum, auto


class RetryStrategy(Enum):
    SELECT = auto()
    TRY_TWICE = auto()
    SOCKET_TIMEOUT = auto()
