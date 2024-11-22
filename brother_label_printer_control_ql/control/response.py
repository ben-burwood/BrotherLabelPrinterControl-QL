from dataclasses import dataclass
from logging import Logger

from brother_label_printer_control_ql.control.constants import (
    RESP_BYTE_NAMES,
    RespMediaTypes,
    RespPhaseTypes,
    RespStatusTypes,
)

from .errors import RespErrorInformation1, RespErrorInformation2
from ..utils.hex import hex_format

@dataclass(frozen=True)
class PrinterResponse:
    status_type: RespStatusTypes
    phase_type: RespPhaseTypes
    media_type: RespMediaTypes
    media_width: int
    media_length: int
    errors: list[str]

    @staticmethod
    def from_bytes(data: bytes, logger: Logger) -> "PrinterResponse":
        data = bytes(data)

        if len(data) < 32:
            raise NameError("Insufficient amount of data received", hex_format(data))
        if not data.startswith(b"\x80\x20\x42"):
            raise NameError("Printer response doesn't start with the usual header (80:20:42)", hex_format(data))

        for i, byte_name in enumerate(RESP_BYTE_NAMES):
            logger.debug("Byte %2d %24s %02X", i, byte_name + ":", data[i])

        errors = []
        error_info_1 = data[8]
        error_info_2 = data[9]
        if error1 := RespErrorInformation1.check_for_error(error_info_1):
            logger.error("Error: " + error1.name)
            errors.append(error1.name)
        if error2 := RespErrorInformation2.check_for_error(error_info_2):
            logger.error("Error: " + error2.name)
            errors.append(error2.name)

        media_width = data[10]
        media_length = data[17]

        media_type = data[11]
        try:
            media_type = RespMediaTypes(media_type)
            logger.debug("Media type: %s", media_type.name)
        except ValueError:
            logger.error("Unknown media type %02X", media_type)

        status_type = data[18]
        try:
            status_type = RespStatusTypes(status_type)
            logger.debug("Status type: %s", status_type.name)
        except ValueError:
            logger.error("Unknown status type %02X", status_type)

        phase_type = data[19]
        try:
            phase_type = RespPhaseTypes(phase_type)
            logger.debug("Phase type: %s", phase_type.name)
        except ValueError:
            logger.error("Unknown phase type %02X", phase_type)

        return PrinterResponse(
            status_type=status_type,
            phase_type=phase_type,
            media_type=media_type,
            media_width=media_width,
            media_length=media_length,
            errors=errors,
        )
