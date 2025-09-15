# utils.py
from pathlib import Path
from typing import List


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