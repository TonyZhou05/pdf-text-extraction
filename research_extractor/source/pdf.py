import os
import dotenv
from pathlib import Path
from typing import Optional

from ..domains.models import Document
from ..source.base import TextSource

dotenv.load_dotenv()


class PDFSource(TextSource):

    def __init__(self, text_file_path: str):
        self.text_file = Path(text_file_path)

        # Check if text file exists
        if not self.text_file.exists():
            raise FileNotFoundError(f"Text file not found: {text_file_path}")

        self.metaData = {"text_file": str(self.text_file), "file_type": "pdf_text"}

    def load(self) -> Document:
        try:
            # Read the text file
            with open(self.text_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract the actual text content (skip header metadata)
            lines = content.split("\n")
            text_lines = []
            skip_header = True

            for line in lines:
                # Speficially skip the header metadata based on the logic in the pdf_to_text_converter.py file
                if line.startswith("=" * 50):
                    skip_header = False
                    continue
                if not skip_header:
                    text_lines.append(line)

            self._text = "\n".join(text_lines).strip()

            # Add additional metadata
            self.metaData.update(
                {
                    "text_length": len(self._text),
                    "text_file_size": self.text_file.stat().st_size,
                }
            )

            return Document(
                doc_id=self.text_file.stem, text=self._text, meta=self.metaData
            )

        except Exception as e:
            raise Exception(f"Failed to read text file {self.text_file}: {str(e)}")

    def get_text(self) -> str:
        if not hasattr(self, "_text"):
            self.load()
        return self._text

    def get_text_file_path(self) -> str:
        return str(self.text_file)
