#!/usr/bin/env python3
"""
PDF to Text Converter using pdfplumber

This script converts PDF files to text format and saves them to a specified directory.
It processes all PDFs in the input directory and creates corresponding .txt files.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import pdfplumber
from tqdm import tqdm


class PDFToTextConverter:

    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize the converter.

        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save extracted text files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        # Validate input directory
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        try:
            text_parts = []

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_parts.append(
                                f"--- Page {page_num + 1} ---\n{page_text}"
                            )
                    except Exception as e1:
                        print(
                            f"Warning: Could not extract text from page {page_num + 1} of {pdf_path.name}: {e1}"
                        )
                        continue

            return "\n\n".join(text_parts) if text_parts else None

        except Exception as e2:
            print(f"Error processing {pdf_path.name}: {e2}")
            return None

    def get_pdf_files(self) -> List[Path]:
        """Get list of PDF files in the input directory."""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        return pdf_files

    def convert_pdf_to_text(self, pdf_path: Path) -> bool:
        """Convert a single PDF to text and save to output directory."""
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)

        if text is None:
            return False

        # Create output filename
        output_filename = pdf_path.stem + ".txt"
        output_path = self.output_dir / output_filename

        # Save text to file
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"Source: {pdf_path.name}\n")
                f.write(f"Extracted on: {os.popen('date').read().strip()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(text)

            return True

        except Exception as e:
            print(f"Error saving text file {output_filename}: {e}")
            return False

    def convert_all_pdfs(self, verbose: bool = True, resume: bool = True) -> dict:
        """
        Convert all PDFs in the input directory to text files.
        """
        pdf_files = self.get_pdf_files()

        if not pdf_files:
            print(f"No PDF files found in {self.input_dir}")
            return {"total": 0, "successful": 0, "failed": 0, "files": []}

        # Filter out already converted files if resume is True
        if resume:
            existing_files = set(f.stem for f in self.output_dir.glob("*.txt"))
            original_count = len(pdf_files)
            pdf_files = [f for f in pdf_files if f.stem not in existing_files]
            if original_count != len(pdf_files):
                print(
                    f"Skipping {original_count - len(pdf_files)} already converted files"
                )

        if not pdf_files:
            print("All PDFs have already been converted!")
            return {"total": 0, "successful": 0, "failed": 0, "files": []}

        print(f"Found {len(pdf_files)} PDF files to convert")
        print(f"Input directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")
        print("-" * 50)

        successful = 0
        failed = 0
        failed_files = []

        # Process files with progress bar
        for pdf_path in tqdm(pdf_files, desc="Converting PDFs", disable=not verbose):
            if self.convert_pdf_to_text(pdf_path):
                successful += 1
                if verbose:
                    print(f"✓ Converted: {pdf_path.name}")
            else:
                failed += 1
                failed_files.append(pdf_path.name)
                if verbose:
                    print(f"✗ Failed: {pdf_path.name}")

        # Print summary
        print("\n" + "=" * 50)
        print("CONVERSION SUMMARY")
        print("=" * 50)
        print(f"Total PDFs processed: {len(pdf_files)}")
        print(f"Successfully converted: {successful}")
        print(f"Failed conversions: {failed}")

        if failed_files:
            print(f"\nFailed files:")
            for filename in failed_files:
                print(f"  - {filename}")

        return {
            "total": len(pdf_files),
            "successful": successful,
            "failed": failed,
            "files": failed_files,
        }


def main():
    """Main function to run the PDF to text converter."""
    parser = argparse.ArgumentParser(
        description="Convert PDF files to text using pdfplumber",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all PDFs in data/pdfs to text files in outputs/text
  python pdf_to_text_converter.py data/pdfs outputs/text
  
  # Convert with custom input and output directories
  python pdf_to_text_converter.py /path/to/pdfs /path/to/output
        """,
    )

    parser.add_argument("input_dir", help="Directory containing PDF files to convert")

    parser.add_argument("output_dir", help="Directory to save extracted text files")

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output and detailed logging",
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't resume from already converted files (reconvert all)",
    )

    args = parser.parse_args()

    try:
        converter = PDFToTextConverter(args.input_dir, args.output_dir)

        # Convert all PDFs
        results = converter.convert_all_pdfs(
            verbose=not args.quiet, resume=not args.no_resume
        )

        # Exit with appropriate code
        if results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# # Convert all PDFs (resumes from where it left off)
#    python pdf_to_text_converter.py research_extractor/data/pdfs research_extractor/data/text

#    # Convert with quiet mode
#    python pdf_to_text_converter.py research_extractor/data/pdfs research_extractor/data/pdfs --quiet

#    # Reconvert all files (don't resume)
#    python pdf_to_text_converter.py research_extractor/data/pdfs research_extractor/data/pdfs --no-resume
