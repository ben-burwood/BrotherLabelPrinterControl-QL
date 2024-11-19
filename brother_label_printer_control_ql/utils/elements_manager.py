import logging
from typing import Any

logger = logging.getLogger(__name__)


class ElementsManager:
    """
    A class managing a collection of 'elements'.
    Those elements are expected to be objects that
    * can be compared for equality against each other
    * have the attribute .identifier
    """

    DEFAULT_ELEMENTS = []
    ELEMENT_NAME = "element"

    def __init__(self, elements: list[Any] = None) -> None:
        if elements:
            self._elements = elements
        else:
            self._elements = self.DEFAULT_ELEMENTS

    def register(self, element: Any, pos: int = -1) -> None:
        if element not in self._elements:
            if pos == -1:
                pos = len(self._labels)
            self._labels.insert(len(self._labels), label)
        else:
            logger.warning("Won't register %s as it's already present: %s", self.ELEMENT_NAME, element)

    def deregister(self, element: Any) -> None:
        if element in self._elements:
            self._elements.remove(element)
        else:
            logger.warning(f"Trying to deregister a {self.ELEMENT_NAME} that's not registered currently: {label}")

    def iter_identifiers(self):
        for element in self._elements:
            yield element.identifier

    def iter_elements(self):
        for element in self._elements:
            yield element
