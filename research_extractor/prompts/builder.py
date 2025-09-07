from .prompt import EXTRACTION_PROMPT
from ..domains.models import Document


class PromptBuilder:
    def __init__(self, doc: Document, fields=[]) -> None:
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
            ]
        self.paper_content = doc.text

    def build_prompt(self) -> str:
        fields_text = "\n".join(
            [
                f'<field id={idx+1}>"{field}"</field>'
                for idx, field in enumerate(self.fields)
            ]
        )
        # print(
        #     "prompt:",
        #     EXTRACTION_PROMPT.format(
        #         paper_content=self.paper_content, fields=fields_text
        #     ),
        # )
        return EXTRACTION_PROMPT.format(
            paper_content=self.paper_content, fields=fields_text
        )
