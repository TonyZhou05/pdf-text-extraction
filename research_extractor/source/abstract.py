from typing import List
from .base import TextSource
from ..domains.models import Document


class AbstractSource(TextSource):
    def __init__(
        self,
        abstract: str,
        title: str = "",
        year: str = "",
        pub_type: str = "",
    ):
        self.abstract = abstract
        self.metaData = {
            "title": title,
            "year": year,
            "pub_type": pub_type,
        }

    def load(self):
        return Document(doc_id="abstract", text=self.abstract, meta=self.metaData)
