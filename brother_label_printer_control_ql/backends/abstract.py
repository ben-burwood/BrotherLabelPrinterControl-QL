import logging
import time
from abc import ABC, abstractmethod
from builtins import bytes

from ..control.constants import RespPhaseTypes, RespStatusTypes
from ..control.outcome import PrintOutcome
from ..control.response import PrinterResponse
from ..control.status import SendStatus

logger = logging.getLogger(__name__)


class BaseBrotherQLBackend(ABC):

    @abstractmethod
    def __init__(self, device_specifier: str = None) -> None:
        pass

    @abstractmethod
    def _read(self, length: int = 32) -> bytes:
        pass

    @abstractmethod
    def _write(self, data: bytes) -> None:
        pass

    @abstractmethod
    def _dispose(self) -> None:
        pass

    def read(self, length: int = 32) -> bytes:
        try:
            ret_bytes = self._read(length)
            if ret_bytes:
                logger.debug("Read %d bytes.", len(ret_bytes))
            return ret_bytes
        except Exception as e:
            logger.debug("Error reading... %s", e)
            raise

    def write(self, data: bytes) -> None:
        logger.debug("Writing %d bytes.", len(data))
        self._write(data)

    def dispose(self) -> None:
        try:
            self._dispose()
        except NotImplementedError:
            pass

    def __del__(self):
        self.dispose()

    def send(self, instructions: bytes, blocking: bool = True) -> SendStatus:
        """
        Send instruction bytes to a printer.

        :param bytes instructions: The instructions to be sent to the printer.
        :param bool blocking: Indicates whether the function call should block while waiting for the completion of the printing.
        """
        status = SendStatus()

        start = time.time()
        logger.info("Sending instructions to the printer. Total: %d bytes.", len(instructions))
        self.write(instructions)
        status.outcome = PrintOutcome.SENT

        if not blocking:
            return status

        while time.time() - start < 10:
            data = self.read()
            if not data:
                time.sleep(0.005)
                continue
            try:
                result = PrinterResponse.from_bytes(data, logger)
            except ValueError:
                logger.error("TIME %.3f - Couldn't understand response: %s", time.time() - start, data)
                continue
            status.printer_state = result
            logger.debug("TIME %.3f - result: %s", time.time() - start, result)
            if result.errors:
                logger.error("Errors occurred: %s", result.errors)
                status.outcome = PrintOutcome.ERROR
                break
            if result.status_type == RespStatusTypes.PRINTING_COMPLETED:
                status.did_print = True
                status.outcome = PrintOutcome.PRINTED
            if result.status_type == RespStatusTypes.PHASE_CHANGE and result.phase_type == RespPhaseTypes.WAITING_TO_RECEIVE:
                status.ready_for_next_job = True
            if status.did_print and status.ready_for_next_job:
                break

        status.log_status(logger)
        return status

    @staticmethod
    @abstractmethod
    def list_available_devices() -> list[str]:
        """List all available devices (by Identifier) for the Backend"""
        pass
