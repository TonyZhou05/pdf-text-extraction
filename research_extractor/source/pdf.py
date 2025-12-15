import os
import dotenv
from pathlib import Path
from typing import Optional
from lxml import etree

from ..domains.models import Document
from ..source.base import TextSource

dotenv.load_dotenv()


class PDFSource(TextSource):

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

        # Check if text file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        self.metaData = {"text_file": str(self.file_path), "file_type": "pdf_text"}

    def get_text(self) -> str:
        if not hasattr(self, "_text"):
            self.load()
        return self._text

    def get_file_path(self) -> str:
        return str(self.file_path)

    def get_segments_from_tei(self):
        """
        Convert GROBID TEI XML into [SourceID]-tagged text segments.
        """
        parser = etree.XMLParser(recover=True)

        try:
            # Load TEI file into string representation
            with open(self.file_path, "r", encoding="utf-8") as f:
                tei_xml = f.read()

            root = etree.fromstring(tei_xml.encode("utf-8"))
            ns = {"tei": "http://www.tei-c.org/ns/1.0"}

            body = root.find(".//tei:text/tei:body", ns)
            if body is None:
                return ""

            segments = []
            source_id = 1

            for div in body.findall("tei:div", ns):
                heading_el = div.find("tei:head", ns)
                heading = (
                    heading_el.text.strip() if heading_el is not None else "Untitled"
                )
                paras = [
                    "".join(p.itertext()).strip() for p in div.findall("tei:p", ns)
                ]
                div_text = "\n".join([p for p in paras if p])

                if div_text.strip():
                    segments.append(
                        f"[SourceID: {source_id}] {heading}\n{div_text.strip()}"
                    )
                    source_id += 1
        except Exception as e:
            print(f"Error parsing TEI XML {self.file_path}: {e}")
            return ""
        # result_text = "\n\n".join(segments)
        # with open("test_output.txt", "w", encoding="utf-8") as f:
        #     f.write(result_text)

        return "\n\n".join(segments)

    def load(self) -> Document:
        self._text = self.get_segments_from_tei()
        self.metaData.update(
            {
                "text_length": len(self._text),
                "text_file_size": self.file_path.stat().st_size,
            }
        )

        return Document(doc_id=self.file_path.stem, text=self._text, meta=self.metaData)
