from pdf2image import convert_from_path
from typing import List, Tuple
from PIL import Image

class PDFProcessor:
    def __init__(self, dpi=300):
        # 300 DPI is the sweet spot for OCR/Table detection
        self.dpi = dpi

    def convert_to_images(self, pdf_path: str) -> List[Tuple[int, Image.Image]]:
        """
        Converts a PDF into a list of PIL Images.
        Returns: List of tuples (page_number, image_object)
        """
        print(f"Converting PDF: {pdf_path}...")
        try:
            # This converts all pages. 
            # You can use first_page/last_page params to limit it.
            images = convert_from_path(pdf_path, dpi=self.dpi)
            
            # print(f"Successfully converted {len(images)} pages.")
            
            # Return with page numbers (1-indexed) for tracking
            return [(i+1, img) for i, img in enumerate(images)]
            
        except Exception as e:
            print(f"Error converting PDF: {e}")
            return []