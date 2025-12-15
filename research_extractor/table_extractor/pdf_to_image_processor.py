from pdf2image import convert_from_path
from typing import List, Tuple
from PIL import Image

class PDFProcessor:
    def __init__(self, dpi=300):
        self.dpi = dpi

    def convert_to_images(self, pdf_path: str) -> List[Tuple[int, Image.Image]]:
        """
        Converts a PDF into a list of PIL Images.
        Returns: List of tuples (page_number, image_object)
        """
        print(f"Converting PDF: {pdf_path}...")
        try:
            images = convert_from_path(pdf_path, dpi=self.dpi)
            return [(i+1, img) for i, img in enumerate(images)]
            
        except Exception as e:
            print(f"Error converting PDF: {e}")
            return []