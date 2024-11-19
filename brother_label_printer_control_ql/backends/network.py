"""
Backend to support Brother QL-series printers via network.
Works cross-platform.
"""

import socket
import time

import select

from .abstract import BaseBrotherQLBackend
from .retry_strategies import RetryStrategy

class BrotherQLBackendNetwork(BaseBrotherQLBackend):
    """
    BrotherQL backend using the Linux Kernel USB Printer Device Handles
    """

    RETRY_STRATEGY = RetryStrategy.SOCKET_TIMEOUT

    READ_TIMEOUT = 0.01

    def __init__(self, device_specifier: str) -> None:
        """
        device_specifier: string or os.open(): identifier in the \
            format file:///dev/usb/lp0 or os.open() raw device handle.
        """
        if isinstance(device_specifier, str):
            host, port = BrotherQLBackendNetwork.extract_host_port_from_device_identifier(device_specifier)

            # try:
            asocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            asocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            asocket.connect((host, port))
            # except OSError as e:
            #    raise ValueError('Could not connect to the device.')

            asocket.settimeout(self.get_socket_timeout_for_retry_strategy())
            self.s = asocket

        elif isinstance(device_specifier, int):
            self.dev = device_specifier
        else:
            raise NotImplementedError("Currently the printer can be specified either via an appropriate string or via an os.open() handle.")

    def _read(self, length: int = 32) -> bytes:
        if self.RETRY_STRATEGY in [RetryStrategy.SOCKET_TIMEOUT, RetryStrategy.TRY_TWICE]:
            if self.RETRY_STRATEGY == RetryStrategy.SOCKET_TIMEOUT:
                tries = 1
            if self.RETRY_STRATEGY == RetryStrategy.TRY_TWICE:
                tries = 2

            for i in range(tries):
                try:
                    data = self.s.recv(length)
                    return data
                except socket.timeout:
                    pass
            return b""
        elif self.RETRY_STRATEGY == RetryStrategy.SELECT:
            data = b""
            start = time.time()
            while (not data) and (time.time() - start < self.READ_TIMEOUT):
                result, _, _ = select.select([self.s], [], [], 0)
                if self.s in result:
                    data += self.s.recv(length)
                if data:
                    break
                time.sleep(0.001)
            return data
        else:
            raise NotImplementedError("Unsupported Retry Strategy")

    def _write(self, data: bytes) -> None:
        self.s.settimeout(10)
        self.s.sendall(data)
        self.s.settimeout(self.READ_TIMEOUT)

    def _dispose(self) -> None:
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()

    @staticmethod
    def list_available_devices() -> list[str]:
        """
        List all available devices for the network backend

        returns: devices: a list of dictionaries with the keys 'identifier' and 'instance': \
            [ {'identifier': 'tcp://hostname[:port]', 'instance': None}, ] \
            Instance is set to None because we don't want to connect to the device here yet.
        """

        # We need some snmp request sent to 255.255.255.255 here
        raise NotImplementedError()
        return ["tcp://" + path for path in paths]

    @staticmethod
    def extract_host_port_from_device_identifier(device_identifier: str) -> tuple[str, int]:
        device_identifier.lstrip("tcp://")

        host, _, port = device_identifier.partition(":")
        port = int(port) if port else 9100
        return host, port

    def get_socket_timeout_for_retry_strategy(self):
        if self.RETRY_STRATEGY in [RetryStrategy.SOCKET_TIMEOUT, RetryStrategy.TRY_TWICE]:
            return self.READ_TIMEOUT
        else:
            return 0
