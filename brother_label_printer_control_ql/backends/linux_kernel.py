"""
Backend to support Brother QL-series printers via the linux kernel USB printer interface.
Works on Linux.
"""

import glob
import os
import time

import select

from .abstract import BaseBrotherQLBackend
from .strategies import RetryStrategy


class BrotherQLBackendLinuxKernel(BaseBrotherQLBackend):
    """
    BrotherQL backend using the Linux Kernel USB Printer Device Handles
    """

    RETRY_STRATEGY = RetryStrategy.SELECT
    READ_TIMEOUT = 0.01

    def __init__(self, device_specifier: str) -> None:
        """
        device_specifier: string or os.open(): identifier in the \
            format file:///dev/usb/lp0 or os.open() raw device handle.
        """
        self.dev = BrotherQLBackendLinuxKernel.get_device(device_specifier)
        self.write_dev = self.dev
        self.read_dev = self.dev

    def _read(self, length: int = 32) -> bytes:
        match self.RETRY_STRATEGY:
            case RetryStrategy.TRY_TWICE:
                data = os.read(self.read_dev, length)
                if data:
                    return data
                else:
                    time.sleep(self.READ_TIMEOUT)
                    return os.read(self.read_dev, length)
            case RetryStrategy.SELECT:
                data = b""
                start = time.time()
                while (not data) and (time.time() - start < self.READ_TIMEOUT):
                    result, _, _ = select.select([self.read_dev], [], [], 0)
                    if self.read_dev in result:
                        data += os.read(self.read_dev, length)
                    if data:
                        break
                    time.sleep(0.001)
                if not data:
                    # one last try if still no data:
                    return os.read(self.read_dev, length)
                else:
                    return data
            case _:
                raise NotImplementedError("Unsupported Retry Strategy")

    def _write(self, data: bytes) -> None:
        os.write(self.write_dev, data)

    def _dispose(self) -> None:
        os.close(self.dev)

    @staticmethod
    def list_available_devices() -> list[str]:
        """
        List all available devices for the linux kernel backend

        returns: devices: a list of dictionaries with the keys 'identifier' and 'instance': \
            [ {'identifier': 'file:///dev/usb/lp0', 'instance': None}, ] \
            Instance is set to None because we don't want to open (and thus potentially block) the device here.
        """
        paths = glob.glob("/dev/usb/lp*")

        return ["file://" + path for path in paths]

    @staticmethod
    def get_device(device_identifier: str | int) -> str | int:
        if isinstance(device_identifier, str):
            if device_identifier.startswith("file://"):
                device_identifier = device_identifier[7:]
            return os.open(device_identifier, os.O_RDWR)
        elif isinstance(device_identifier, int):
            return device_identifier
        else:
            raise NotImplementedError("Currently the printer can be specified either via an appropriate string or via an os.open() handle.")
