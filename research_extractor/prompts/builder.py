import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .prompt import EXTRACTION_PROMPT, TREATMENT_EXTRACTION_PROMPT
from ..domains.models import Document
from .batch_fields import BATCH_METADATA, BATCH_DEMOGRAPHICS, BATCH_TREATMENTS, TREATMENT_PROMPT_ADDITION


class PromptBuilder:
    def __init__(self, doc: Document, extracted_tables: Optional[List[Dict[str, Any]]] = None) -> None:
        self.doc_text = doc.text
        self.extracted_tables = extracted_tables or []
        # batches of different categories to be extracted separately
        self.batch_metadata = BATCH_METADATA
        self.batch_demographics = BATCH_DEMOGRAPHICS
        self.batch_treatments = BATCH_TREATMENTS
        
        # Fallback if someone uses the class without categories
        self.all_default_fields = self.batch_metadata + self.batch_demographics + self.batch_treatments

    def build_prompt(self, category: str = "all") -> str:
        """
        Builds a prompt specifically for the requested category.
        Args:
            category: 'metadata', 'demographics', 'treatments', or 'all'
        """
        
        # 1. SELECT FIELDS & SETTINGS BASED ON CATEGORY
        if category == "metadata":
            target_fields = self.batch_metadata
            include_tables = False 
            template = EXTRACTION_PROMPT
            
        elif category == "demographics":
            target_fields = self.batch_demographics
            include_tables = True 
            template = EXTRACTION_PROMPT
            
        elif category == "treatments":
            target_fields = self.batch_treatments
            include_tables = True 
            template = TREATMENT_EXTRACTION_PROMPT

        # shouldn't reach here
        else:
            target_fields = self.all_default_fields
            include_tables = True
            template = EXTRACTION_PROMPT

        fields_text = "\n".join(
            [
                f'<field id={idx+1}>"{field}"</field>'
                for idx, field in enumerate(target_fields)
            ]
        )

        # append the instruction to the fields definition for treatments category
        if category == "treatments":
            fields_text += TREATMENT_PROMPT_ADDITION

        tables_input = ""
        if include_tables and self.extracted_tables:
            # We dump the tables structure into the prompt
            tables_input = ',\n    "extracted_tables": ' + json.dumps(
                self.extracted_tables, ensure_ascii=False
            )

        # 5. GENERATE FINAL PROMPT
        prompt_text = template.format(
            doc_text=self.doc_text, 
            fields=fields_text, 
            tables_input=tables_input
        )
        
        # Debugging / Logging
        print(f"Generated prompt for category: {category}")
        
        # Save to file for inspection (renamed to include category)
        output_filename = f"extraction_prompt_{category}.txt"
        output_path = Path(__file__).resolve().parent.parent / output_filename
        output_path.write_text(prompt_text, encoding="utf-8")

        return prompt_text
