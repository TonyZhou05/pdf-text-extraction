#!/usr/bin/env python3
"""
Helper script to process TEI files from test_TEI folder and extract segmented text.
Each file is processed using get_segments_from_tei() and saved to temp_segmented_text folder.
"""

import os
import sys
from pathlib import Path

# Add the research_extractor module to the path
sys.path.append(str(Path(__file__).parent / "research_extractor"))

from research_extractor.source.pdf import PDFSource


def process_tei_files():
    """Process all TEI files in test_TEI folder and save segmented text."""
    
    # Define paths
    base_dir = Path(__file__).parent
    tei_folder = base_dir / "research_extractor" / "data" / "test_TEI"
    output_folder = base_dir / "temp_segmented_text"
    
    # Create output folder if it doesn't exist
    output_folder.mkdir(exist_ok=True)
    
    # Get all TEI files
    tei_files = list(tei_folder.glob("*.grobid.tei.xml"))
    
    if not tei_files:
        print(f"No TEI files found in {tei_folder}")
        return
    
    print(f"Found {len(tei_files)} TEI files to process")
    
    processed_count = 0
    error_count = 0
    
    for tei_file in tei_files:
        try:
            print(f"Processing: {tei_file.name}")
            
            # Create PDFSource instance and get segmented text
            pdf_source = PDFSource(str(tei_file))
            segmented_text = pdf_source.get_segments_from_tei()
            
            # Create output filename (remove .grobid.tei.xml and add .txt)
            output_filename = tei_file.stem.replace('.grobid.tei', '') + '.txt'
            output_path = output_folder / output_filename
            
            # Save segmented text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(segmented_text)
            
            print(f"  -> Saved to: {output_path}")
            processed_count += 1
            
        except Exception as e:
            print(f"  -> Error processing {tei_file.name}: {e}")
            error_count += 1
    
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {processed_count} files")
    print(f"Errors: {error_count} files")
    print(f"Output folder: {output_folder}")


if __name__ == "__main__":
    process_tei_files()

