"""
Backend to support Brother QL-series printers via PyUSB.
Works on Mac OS X and Linux.

Requires PyUSB: https://github.com/walac/pyusb/
Install via `pip install pyusb`
"""

import time

import usb.core
import usb.util
from select import select

from .abstract import BaseBrotherQLBackend
from .retry_strategies import RetryStrategy

class BrotherQLBackendPyUSB(BaseBrotherQLBackend):
    """
    BrotherQL backend using PyUSB
    """

    RETRY_STRATEGY = RetryStrategy.TRY_TWICE

    READ_TIMEOUT = 10.0  # ms
    WRITE_TIMEOUT = 15000.0  # ms

    def __init__(self, device_specifier: str) -> None:
        """
        device_specifier: string or pyusb.core.Device: identifier of the \
            format usb://idVendor:idProduct/iSerialNumber or pyusb.core.Device instance.
        """
        vendor, product, serial = BrotherQLBackendPyUSB.extract_vendor_product_serial_from_device_identifier(device_specifier)

        self.dev: usb.core.Device | None = None
        for device in BrotherQLBackendPyUSB.list_available_devices_as_usb():
            if device.idVendor == vendor and device.idProduct == product or (serial and device.iSerialNumber == serial):
                self.dev = device
                break

        if self.dev is None:
            raise ValueError("Device not found")

        try:
            assert self.dev.is_kernel_driver_active(0)
            self.dev.detach_kernel_driver(0)
            self.was_kernel_driver_active = True
        except (NotImplementedError, AssertionError):
            self.was_kernel_driver_active = False

        # set the active configuration. With no arguments, the first configuration will be the active one
        self.dev.set_configuration()

        cfg = self.dev.get_active_configuration()
        intf = usb.util.find_descriptor(cfg, bInterfaceClass=7)
        assert intf is not None

        ep_match_in = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        ep_match_out = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT

        ep_in = usb.util.find_descriptor(intf, custom_match=ep_match_in)
        ep_out = usb.util.find_descriptor(intf, custom_match=ep_match_out)

        assert ep_in is not None
        assert ep_out is not None

        self.write_dev = ep_out
        self.read_dev = ep_in

    def _raw_read(self, length: int = 32) -> bytes:
        # pyusb Device.read() operations return array() type - convert it to bytes()
        return bytes(self.read_dev.read(length))

    def _read(self, length: int = 32) -> bytes:
        match self.RETRY_STRATEGY:
            case RetryStrategy.TRY_TWICE:
                data = self._raw_read(length)
                if data:
                    return bytes(data)
                else:
                    time.sleep(self.READ_TIMEOUT / 1000.0)
                    return self._raw_read(length)
            case RetryStrategy.SELECT:
                data = b""
                start = time.time()
                while (not data) and (time.time() - start < self.READ_TIMEOUT / 1000.0):
                    result, _, _ = select([self.read_dev], [], [], 0)
                    if self.read_dev in result:
                        data += self._raw_read(length)
                    if data:
                        break
                    time.sleep(0.001)
                if not data:
                    # one last try if still no data:
                    return self._raw_read(length)
                else:
                    return data
            case _:
                raise NotImplementedError("Unsupported Retry Strategy")

    def _write(self, data: bytes) -> None:
        self.write_dev.write(data, int(self.WRITE_TIMEOUT))

    def _dispose(self) -> None:
        usb.util.dispose_resources(self.dev)
        del self.write_dev, self.read_dev
        if self.was_kernel_driver_active:
            self.dev.attach_kernel_driver(0)
        del self.dev

    @staticmethod
    def list_available_devices_as_usb() -> list[usb.core.Device]:
        class USBFindClass:
            def __init__(self, class_):
                self._class = class_

            def __call__(self, device):
                if device.bDeviceClass == self._class:
                    return True
                # ok, transverse all devices to find an interface that matches our class
                for cfg in device:
                    intf = usb.util.find_descriptor(cfg, bInterfaceClass=self._class)
                    if intf is not None:
                        return True
                return False

        BROTHER_VENDOR_ID = 0x04F9
        return [d for d in usb.core.find(find_all=1, custom_match=USBFindClass(7), idVendor=BROTHER_VENDOR_ID)]

    @staticmethod
    def list_available_devices() -> list[str]:
        """
        List all available devices for the respective backend

        returns: devices: a list of dictionaries with the keys 'identifier' and 'instance': \
            [ {'identifier': 'usb://0x04f9:0x2015/C5Z315686', 'instance': pyusb.core.Device()}, ]
            The 'identifier' is of the format idVendor:idProduct_iSerialNumber.
        """

        def extract_identifier(dev: usb.Device) -> str:
            try:
                serial = usb.util.get_string(dev, 256, dev.iSerialNumber)
                return "usb://0x{:04x}:0x{:04x}_{}".format(dev.idVendor, dev.idProduct, serial)
            except:
                return "usb://0x{:04x}:0x{:04x}".format(dev.idVendor, dev.idProduct)

        return [extract_identifier(printer) for printer in BrotherQLBackendPyUSB.list_available_devices_as_usb()]

    @staticmethod
    def extract_vendor_product_serial_from_device_identifier(device_identifier: str) -> tuple[int, int, str]:
        device_identifier.lstrip("usb://")
        vendor_product, _, serial = device_identifier.partition("/")
        vendor, _, product = vendor_product.partition(":")
        vendor, product = int(vendor, 16), int(product, 16)
        return vendor, product, serial
