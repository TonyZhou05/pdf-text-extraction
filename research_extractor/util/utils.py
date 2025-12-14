# utils.py
from pathlib import Path
from typing import List, Optional, Tuple


def get_text_files_from_directory(directory: Path) -> List[Path]:
    """
    Get all .txt files from a directory.

    Args:
        directory: Directory containing text files

    Returns:
        List of Path objects for text files
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    text_files = list(directory.glob("*.txt"))
    if not text_files:
        raise ValueError(f"No .txt files found in directory: {directory}")

    return sorted(text_files)


def get_xml_files_from_directory(directory: Path) -> List[Path]:
    """
    Get all .xml files from a directory.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    xml_files = list(directory.glob("*.xml"))
    if not xml_files:
        raise ValueError(f"No .xml files found in directory: {directory}")

    return sorted(xml_files)


def get_pdf_file_for_xml(xml_file: Path) -> Optional[Path]:
    """
    Get the corresponding PDF file for an XML file (same name, .pdf extension).
    
    Args:
        xml_file: Path to XML file
        
    Returns:
        Path to corresponding PDF file if it exists, None otherwise
    """
    pdf_file = xml_file.with_suffix(".pdf")
    if pdf_file.exists():
        return pdf_file

    # Fallback: split on the first dot and use the leading token.
    # This covers names like 8519675.grobid.tei.xml -> 8519675.pdf
    leading_token = xml_file.name.split(".")[0]
    candidate = xml_file.with_name(f"{leading_token}.pdf")
    if candidate.exists():
        return candidate

    return None


def get_xml_pdf_pairs_from_directory(directory: Path) -> List[Tuple[Path, Optional[Path]]]:
    """
    Get all XML files from a directory and their corresponding PDF files (if they exist).
    
    Args:
        directory: Directory containing XML and PDF files
        
    Returns:
        List of tuples (xml_file, pdf_file) where pdf_file is None if not found
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    xml_files = list(directory.glob("*.xml"))
    if not xml_files:
        raise ValueError(f"No .xml files found in directory: {directory}")

    pairs = []
    for xml_file in sorted(xml_files):
        pdf_file = get_pdf_file_for_xml(xml_file)
        pairs.append((xml_file, pdf_file))
    
    return pairs
