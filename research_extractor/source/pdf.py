import os
import dotenv
from pypdf import PdfReader

from ..domains.models import Document
from ..source.base import TextSource

dotenv.load_dotenv()


# TODO: need to finalize the design of this class later
class PDFSource(TextSource):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metaData = {"source": file_path}

    def load(self) -> Document:
        reader = PdfReader(self.file_path)
        self._text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return Document(
            doc_id=os.path.basename(self.file_path), text=self._text, meta=self.metaData
        )
