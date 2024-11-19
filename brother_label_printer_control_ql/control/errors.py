from enum import IntEnum


class RespErrorInformation1(IntEnum):
    NO_MEDIA_WHEN_PRINTING = 0
    END_OF_MEDIA = 1  # DieCut size only
    TAPE_CUTTER_JAM = 2
    NOT_USED = 3
    MAIN_UNIT_IN_USE = 4  # QL-560/650TD/1050
    PRINTER_TURNED_OFF = 5
    HIGH_VOLTAGE_ADAPTER = 6  # NOT USED
    FAN_DOESNT_WORK = 7  # QL-1050/1060N

    def is_present(self, error_info: int) -> bool:
        return bool(error_info & (1 << self.value))

    @staticmethod
    def check_for_error(error_info: int) -> "RespErrorInformation1 | None":
        for error in RespErrorInformation1:
            if error.is_present(error_info):
                return error
        return None


class RespErrorInformation2(IntEnum):
    REPLACE_MEDIA_ERROR = 0
    EXPANSION_BUFFER_FULL = 1
    TRANSMISSION_COMMUNICATION_ERROR = 2
    COMMUNICATION_BUFFER_FULL = 3  # NOT USED
    COVER_OPENED_WHILE_PRINTING = 4  # Except QL-500
    CANCEL_KEY = 5  # NOT USED
    MEDIA_CANNOT_BE_FED = 6  # Also when the media end is detected
    SYSTEM_ERROR = 7

    def is_present(self, error_info: int) -> bool:
        return bool(error_info & (1 << self.value))

    @staticmethod
    def check_for_error(error_info: int) -> "RespErrorInformation2 | None":
        for error in RespErrorInformation2:
            if error.is_present(error_info):
                return error
        return None
