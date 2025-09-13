from abc import ABC, abstractmethod
from ..domains.models import Document


class TextSource(ABC):
    @abstractmethod
    def load(self) -> Document:
        raise NotImplementedError("Should implement this method")
