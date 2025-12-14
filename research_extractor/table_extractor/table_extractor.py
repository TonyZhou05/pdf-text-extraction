import torch
import base64
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
from transformers import AutoImageProcessor, TableTransformerForObjectDetection
from .pdf_to_image_processor import PDFProcessor
from .table_analyzer import TableAnalyzer

class TableExtractor:
    def __init__(self, model_name="microsoft/table-transformer-detection"):
        """
        Initializes the model and processor once to avoid reloading overhead.
        """
        print(f"Loading model: {model_name}...")
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = TableTransformerForObjectDetection.from_pretrained(model_name)
        self.pdf_processor = PDFProcessor()
        print("Model loaded successfully.")

    def _encode_image_to_base64(self, pil_image):
        """
        Internal helper: Converts a PIL Image to a Base64 string.
        """
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def extract(self, image_input, threshold=0.9, padding=20):
        """
        Main method:
        1. Detects tables in the image.
        2. Crops them with padding.
        3. Encodes them to Base64.
        
        Args:
            image_input: Either a file path (str/Path) or a PIL.Image object
            threshold: Confidence threshold for table detection
            padding: Padding around detected tables in pixels
        
        Returns:
        A list of dictionaries, where each dictionary represents a detected table:
        [
            {
                "id": 1,
                "confidence": 0.99,
                "box_coords": [x, y, x, y],
                "image": <PIL.Image Object>,
                "base64": "data:image/jpeg;base64/..."
            },
            ...
        ]
        """
        # 1. Load and Preprocess
        if isinstance(image_input, (str, Path)):
            image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")
        else:
            raise ValueError(f"image_input must be a file path or PIL.Image, got {type(image_input)}")
        
        inputs = self.processor(images=image, return_tensors="pt")

        # 2. Model Inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # 3. Post-processing (Convert to boxes)
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, threshold=threshold, target_sizes=target_sizes
        )[0]

        extracted_tables = []

        # 4. Loop through detections
        if len(results['boxes']) == 0:
            print("No tables detected.")
            return extracted_tables

        print(f"Detected {len(results['boxes'])} table(s). Processing...")

        for i, (score, label, box) in enumerate(zip(results["scores"], results["labels"], results["boxes"])):
            # Only process if label is 'table' (some models detect columns too, though this one is mostly tables)
            # The microsoft detection model usually only has label 0 for table.
            
            # Convert box to list
            xmin, ymin, xmax, ymax = box.tolist()

            # Apply Padding (with boundary checks)
            left   = max(0, xmin - padding)
            top    = max(0, ymin - padding)
            right  = min(image.width, xmax + padding)
            bottom = min(image.height, ymax + padding)

            # Crop
            cropped_img = image.crop((left, top, right, bottom))

            # Persist cropped image to project root for inspection
            project_root = Path(__file__).resolve().parents[2]
            output_path = project_root / f"picture_{i+1}.jpg"
            try:
                cropped_img.save(output_path, format="JPEG")
            except Exception as e:
                print(f"Warning: failed to save cropped image {output_path}: {e}")

            # Encode (The requirement from Bullet Point 1)
            b64_string = self._encode_image_to_base64(cropped_img)

            table_analyzer = TableAnalyzer()

            prompt = """
                Analyze this clinical table image.
                1. Identify the column headers (e.g., Treatment Group vs Placebo).
                2. Extract the row data into a JSON list of objects.
                3. If values have confidence intervals (e.g. "15.4 (12.0-18.1)"), keep them as strings.
            """
            table_extracted = table_analyzer.analyze(b64_string, prompt)

            # Store result
            table_data = {
                "id": i + 1,
                "confidence": round(score.item(), 4),
                "original_box": [round(x, 2) for x in box.tolist()],
                "cropped_box": [round(left, 2), round(top, 2), round(right, 2), round(bottom, 2)],
                "image": cropped_img,        # Useful if you want to save to disk later
                "table_extracted": table_extracted        # Useful for sending to LLM
            }
            extracted_tables.append(table_data)
            
            print(f"Table {i+1} processed (Confidence: {table_data['confidence']})")

        return extracted_tables

    def extract_from_pdf(
        self, 
        pdf_path: str, 
        threshold: float = 0.9, 
        padding: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF file by converting pages to images and detecting tables.
        
        Args:
            pdf_path: Path to the PDF file
            threshold: Confidence threshold for table detection
            padding: Padding around detected tables in pixels
            
        Returns:
            List of dictionaries containing extracted table information:
            [
                {
                    "page": 1,
                    "table_id": 1,
                    "confidence": 0.99,
                    "base64_binary": "base64_encoded_string",
                    "original_box": [x1, y1, x2, y2],
                    "cropped_box": [x1, y1, x2, y2]
                },
                ...
            ]
        """
        print("extract_from_pdf")
        extracted_tables = []
        pdf_path_obj = Path(pdf_path)
        
        if not pdf_path_obj.exists():
            print(f"Warning: PDF file not found: {pdf_path}")
            return extracted_tables
        
        # Convert PDF to images
        page_images = self.pdf_processor.convert_to_images(str(pdf_path))
        
        # Extract tables from each page
        for page_num, page_image in page_images:
            tables = self.extract(page_image, threshold=threshold, padding=padding)
            for table in tables:
                # Store the base64 binary data
                extracted_tables.append({
                    "page": page_num,
                    "table_id": table["id"],
                    "table_extracted": table["table_extracted"]
                })
        
        return extracted_tables
