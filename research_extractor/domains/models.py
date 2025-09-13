from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Document:
    doc_id: str
    text: str
    meta: Dict[str, str]
