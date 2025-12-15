EXTRACTION_PROMPT = """You are now the following python function: ```
def extract_fields_from_input_study(inputs: Dict[str, Any]) -> str:
    \"\"\"
    This function is tasked with analyzing clinical trial study reports or papers to extract specific information as structured data
    and provide citations for the extracted information.
    The user will provide a list of fields they are interested in, along with a natural language description for each field to guide you on what content to look for and from which parts of the report to extract it.
2
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
doc_text = \"\"\"{doc_text}\"\"\"
fields = \"\"\"{fields}\"\"\"

inputs = {{
    "doc_text": doc_text,
    "fields": fields
    {tables_input}
}}
Format:
    ```json
    {{  "result": [
        {{ "name": "Study Year", "value": "2023", "source_id": [1] }},
        ...
    ] }}
    ```
"""

TREATMENT_EXTRACTION_PROMPT = """... (Similar Intro) ...

    IMPORTANT FOR SAFETY DATA:
    You are extracting linked events. Do NOT separate DLTs from their Grades.
    Group every adverse event into a single object.
    
    Returns: A syntactically correct JSON string with a "safety_events" key.
        Format:
        ```json
        {{  "safety_events": [
            {{
                "DLT": "Neutropenia",
                "Grade": "3",
                "At_Level": "4",
                "Frequency": "2",
                "Total_Patients": "10",
                "source_id": [5]
            }},
            {{
                "DLT": "Fatigue",
                "Grade": "2",
                ...
            }}
        ] }}
        ```
    
    # User provided inputs
    doc_text = \"\"\"{doc_text}\"\"\"
    fields = \"\"\"{fields}\"\"\"
    
    inputs = {{
        "doc_text": doc_text,
        "fields": fields{tables_input}
    }}
"""


