#!/usr/bin/env python3
"""
Research Value Extractor

A unified script for extracting structured values from research papers.
Supports both abstract-based and full PDF-based extraction.

Usage:
    python research_value_extractor.py --help
"""

import argparse
import json
import re
# import tempfile
import os
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
import io
import dotenv

from util.decoders import ResponseJSONDecoder

dotenv.load_dotenv()

try:
    from pypdf import PdfReader
except ImportError:
    print("Error: pypdf library not found. Install with: pip install pypdf")
    exit(1)

try:
    import openai
    from openai import OpenAI
except ImportError:
    print("Error: openai library not found. Install with: pip install openai")
    exit(1)


class ResearchValueExtractor:
    """
    A unified class for extracting structured values from research papers.
    Supports both abstract-based and full PDF-based extraction.
    """
    
    # Default fields for study characteristic extraction
    DEFAULT_FIELDS = [
        "Study Name, string, the study's alias, usually be in the format of FirstAuthorYear",
        "Study Type, string, if the study is randomized controlled trial, observational study, or others",
        "Study Year, date, the study's year",
        "Location, string, which countries the study was conducted in",
        "Phase, string, in which phase this clinical trial is in, e.g., phase 1, phase 2, phase 3, or phase 4",
        "Conditions, list of string, the conditions or diseases the study is investigating",
        "Treatments, list of string, the primary treatment or intervention used in the study",
        "Comparator, list of string, the comparator treatment or intervention used in the study",
        "Num Patients, int, how many participants are in the study",
        "Mean Age, continuous, the average age of the participants",
        "Age Range, string, the age range of the participants",
    ]
    
    # Extraction prompt template
    EXTRACTION_PROMPT = """You are now the following python function: ```
def extract_fields_from_input_study(inputs: Dict[str, Any]) -> str:
    \"\"\"
    This function is tasked with analyzing clinical trial study reports or papers to extract specific information as structured data
    and provide citations for the extracted information.
    The user will provide a list of fields they are interested in, along with a natural language description for each field to guide you on what content to look for and from which parts of the report to extract it.

    IMPORTANT:
    For each field described by the user, you need to:
    1. Identify and extract the relevant information from the report based on the provided description.
    2. Generate a field name that accurately represents the content of the field based on its description.
    3. Structure the extracted information into a standard format whenever possible (e.g., integer, numerical values, dates, keywords, list of terms). 
        If standardization is not possible, the information should be presented in text format.
        If the field is not found in the report, the extracted value should be "NP".
    4. Provide a reference to the document ID from which this information was extracted.
        This citation id should be restricted to be integers only.
        You should NOT cite more than three sources for a single field.
        You should try your best to provide the most relevant and specific citation for each field.
        If two or more sources are equally relevant, you can just cite them all.

    Returns: A syntactically correct JSON string representing a list of dictionary with three keys: name, value, and source_id.
        Format:
        ```json
        {{  "result": [
            {{
                "name":  \\ str, length <= 25 tokens
                "value":  \\ str, length <= 25 tokens
                "source_id":  \\ list[int], length <= 3 ids
            }},
            {{
                "name":, 
                "value":  \\ str, length <= 25 tokens
                "source_id":  \\ list[int], length <= 3 ids
            }},
                ...
        ]
        }}
        ```
    \"\"\"
```
Respond exclusively with the generated JSON string.

# User provided inputs
paper_content = \"\"\"{paper_content}\"\"\"
fields = \"\"\"{fields}\"\"\"

inputs = {{
    "paper_content": paper_content,
    "fields": fields
}}
"""

    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the ResearchValueExtractor.
        
        Args:
            openai_api_key: OpenAI API key. If None, will use environment variable OPENAI_API_KEY
            model: OpenAI model to use for extraction
        """
        self.model = model

        # Set up OpenAI client
        if openai_api_key:
            self.client = OpenAI(api_key=openai_api_key)
        else:
            print("Using OPENAI_API_KEY from environment variable", os.getenv("OPENAI_API_KEY"))
            
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if not self.client:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")

    def extract_text_from_pdf(self, pdf_path: Union[str, Path, bytes]) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file or PDF content as bytes
            
        Returns:
            Extracted text from the PDF
        """
        try:
            if isinstance(pdf_path, bytes):
                # Handle bytes input
                pdf_file = io.BytesIO(pdf_path)
                reader = PdfReader(pdf_file)
            else:
                # Handle file path input
                pdf_path = Path(pdf_path)
                if not pdf_path.exists():
                    raise FileNotFoundError(f"PDF file not found: {pdf_path}")
                
                with open(pdf_path, 'rb') as f:
                    reader = PdfReader(f)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    # Add page number annotation
                    text_parts.append(f"# Page {page_num + 1}\n{page_text}")
            
            full_text = '\n\n'.join(text_parts)
            
            # Clean up the text
            full_text = self._clean_text(full_text)
            
            return full_text
            
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """
        Clean and process extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Remove page numbers at the bottom of pages (common pattern)
        text = re.sub(r'\n\s*\d+\s*\n$', '', text, flags=re.MULTILINE)
        
        # Clean up line breaks within sentences
        text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', text)
        
        return text.strip()

    def extract_from_abstract(self, 
                            abstract: str, 
                            fields: Optional[List[str]] = None,
                            title: str = "",
                            year: str = "",
                            publication_type: str = "") -> Dict[str, Any]:
        """
        Extract values from an abstract.
        
        Args:
            abstract: Abstract text
            fields: List of fields to extract. If None, uses default fields
            title: Paper title (optional)
            year: Publication year (optional)
            publication_type: Type of publication (optional)
            
        Returns:
            Dictionary containing extraction results
        """
        if fields is None:
            fields = self.DEFAULT_FIELDS
            
        # Format the paper content
        paper_content = self._format_paper_content(
            title=title,
            abstract=abstract,
            year=year,
            publication_type=publication_type
        )
        
        return self._extract_values(paper_content, fields)

    def extract_from_pdf(self, 
                        pdf_path: Union[str, Path, bytes], 
                        fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract values from a full PDF file.
        
        Args:
            pdf_path: Path to PDF file or PDF content as bytes
            fields: List of fields to extract. If None, uses default fields
            
        Returns:
            Dictionary containing extraction results
        """
        if fields is None:
            fields = self.DEFAULT_FIELDS
            
        # Extract text from PDF
        full_text = self.extract_text_from_pdf(pdf_path)
        
        return self._extract_values(full_text, fields)

    def _format_paper_content(self, title: str = "", abstract: str = "", 
                            year: str = "", publication_type: str = "") -> str:
        """
        Format paper content for extraction.
        
        Args:
            title: Paper title
            abstract: Abstract text
            year: Publication year
            publication_type: Type of publication
            
        Returns:
            Formatted paper content
        """
        content_parts = []
        
        if title:
            content_parts.append(f"# Title\n{title}")
        
        if abstract:
            content_parts.append(f"# Abstract\n{abstract}")
        
        if year:
            content_parts.append(f"# Publication Date\n{year}")
        
        if publication_type:
            content_parts.append(f"# Publication Type\n{publication_type}")
        
        return '\n\n'.join(content_parts)

    def _extract_values(self, paper_content: str, fields: List[str]) -> Dict[str, Any]:
        """
        Extract values using LLM.
        
        Args:
            paper_content: Formatted paper content
            fields: List of fields to extract
            
        Returns:
            Dictionary containing extraction results
        """
        # Format fields for the prompt
        fields_text = '\n'.join([f"<field id={idx+1}>\"{field}\"</field>" for idx, field in enumerate(fields)])
        
        # Create the prompt
        prompt = self.EXTRACTION_PROMPT.format(
            paper_content=paper_content,
            fields=fields_text
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse the response
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                result = json.loads(result_text, cls=ResponseJSONDecoder)
                return {
                    "success": True,
                    "result": result,
                    "raw_response": result_text
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw response
                return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_response": result_text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}",
                "raw_response": None
            }

    def extract_single_value(self, 
                           paper_content: str, 
                           field_description: str) -> Dict[str, Any]:
        """
        Extract a single value from paper content.
        
        Args:
            paper_content: Paper content (abstract or full text)
            field_description: Description of the field to extract
            
        Returns:
            Dictionary containing the extracted value
        """
        return self._extract_values(paper_content, [field_description])


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Extract structured values from research papers")
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--abstract", type=str, help="Abstract text to extract from")
    input_group.add_argument("--pdf", type=str, help="Path to PDF file to extract from")
    
    # Extraction options
    parser.add_argument("--fields", type=str, nargs="+", 
                       help="Fields to extract (if not provided, uses default fields)")
    parser.add_argument("--single-field", type=str, 
                       help="Extract a single field (provide description)")
    
    # Paper metadata (for abstract extraction)
    parser.add_argument("--title", type=str, default="", help="Paper title")
    parser.add_argument("--year", type=str, default="", help="Publication year")
    parser.add_argument("--publication-type", type=str, default="", help="Publication type")
    
    # Output options
    parser.add_argument("--output", type=str, help="Output file path (JSON format)")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")
    
    # API options
    parser.add_argument("--api-key", type=str, help="OpenAI API key")
    parser.add_argument("--model", type=str, default="gpt-4o", help="OpenAI model to use")
    
    args = parser.parse_args()
    
    # Initialize extractor
    try:
        extractor = ResearchValueExtractor(
            openai_api_key=args.api_key,
            model=args.model
        )
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Determine fields to extract
    if args.single_field:
        fields = [args.single_field]
    elif args.fields:
        fields = args.fields
    else:
        fields = None
    
    # Perform extraction
    try:
        if args.abstract:
            result = extractor.extract_from_abstract(
                abstract=args.abstract,
                fields=fields,
                title=args.title,
                year=args.year,
                publication_type=args.publication_type
            )
        elif args.pdf:
            result = extractor.extract_from_pdf(
                pdf_path=args.pdf,
                fields=fields
            )
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                if args.pretty:
                    json.dump(result, f, indent=2)
                else:
                    json.dump(result, f)
            print(f"Results saved to {args.output}")
        else:
            if args.pretty:
                print(json.dumps(result, indent=2))
            else:
                print(json.dumps(result))
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
