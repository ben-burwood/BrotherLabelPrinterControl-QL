from enum import Enum
from typing import Type

from .abstract import BaseBrotherQLBackend, logger
from .pyusb import BrotherQLBackendPyUSB

class Backend(Enum):
    PYUSB = "pyusb"
    NETWORK = "network"
    LINUX_KERNEL = "linux_kernel"

    @property
    def printer(self) -> Type[BaseBrotherQLBackend]:
        match self:
            case Backend.PYUSB:
                from . import pyusb as pyusb_backend

                return pyusb_backend.BrotherQLBackendPyUSB
            case Backend.NETWORK:
                from . import network as network_backend

                return network_backend.BrotherQLBackendNetwork
            case Backend.LINUX_KERNEL:
                from . import linux_kernel as linux_kernel_backend

                return linux_kernel_backend.BrotherQLBackendLinuxKernel

    def discover(self) -> list[str]:
        return self.printer.list_available_devices()

    @staticmethod
    def all() -> list[str]:
        return [b.value for b in Backend]

    @staticmethod
    def detect(identifier: str) -> "Backend":
        if identifier.startswith("usb://") or identifier.startswith("0x"):
            return Backend.PYUSB
        elif identifier.startswith("file://") or identifier.startswith("/dev/usb/") or identifier.startswith("lp"):
            return Backend.LINUX_KERNEL
        elif identifier.startswith("tcp://"):
            return Backend.NETWORK
        else:
            raise ValueError(f"Cannot Detect the Backend for identifier: {identifier}")
