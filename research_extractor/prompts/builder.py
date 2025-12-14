import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .prompt import EXTRACTION_PROMPT
from ..domains.models import Document


class PromptBuilder:
    def __init__(self, doc: Document, fields=[], extracted_tables: Optional[List[Dict[str, Any]]] = None) -> None:
        self.fields = fields
        if not self.fields:
            self.fields = [
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
                "DLT, string, dose-limiting toxicity observed (e.g., neutropenia)",
                "Grade, int/string, severity of toxicity, based on CTCAE grading (1–5)",
                "At_Level, int/string, the dose-escalation level where the toxicity was observed (e.g., 4)",
                "Observed_Frequency, int/string, number of patients who experienced the given DLT at that dose level",
                "Total, int/string, total number of patients treated at that dose level",
                "combined_dose_info, string, detailed dose information for that level, including drug names, dosages, and schedules",
                "source_id, list[int], index(es) of the section(s) in the PDF or parsed text where the extracted information was found"
            ]
        self.paper_content = doc.text
        self.extracted_tables = extracted_tables or []

    def build_prompt(self) -> str:
        fields_text = "\n".join(
            [
                f'<field id={idx+1}>"{field}"</field>'
                for idx, field in enumerate(self.fields)
            ]
        )
        print("extracted_tables:", self.extracted_tables)

        tables_input = ""
        if self.extracted_tables:
            tables_input = ',\n    "extracted_tables": ' + json.dumps(
                self.extracted_tables, ensure_ascii=False
            )

        prompt_text = EXTRACTION_PROMPT.format(
            paper_content=self.paper_content, fields=fields_text, tables_input=tables_input
        )
        print(prompt_text)

        # Save the generated prompt to the parent directory of this file (outer directory)
        output_path = Path(__file__).resolve().parent.parent / "extraction_prompt.txt"
        output_path.write_text(prompt_text)

        return prompt_text
