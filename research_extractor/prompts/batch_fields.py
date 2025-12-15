BATCH_METADATA = [
    "Study Name, string, the study's alias (FirstAuthorYear)",
    "Study Type, string, e.g. RCT, observational",
    "Study Year, date",
    "Location, string, countries",
    "Phase, string, e.g. phase 1, phase 2",
    "Conditions, list of string, diseases investigated",
    "Treatments, list of string, primary intervention",
    "Comparator, list of string, control/comparator"
]

BATCH_DEMOGRAPHICS = [
    "Num Patients, int, total participants",
    "Mean Age, continuous, average age",
    "Age Range, string, min-max age"
]

BATCH_TREATMENTS = [
    "combined_dose_info, string, dose details/schedule",
    "DLT, string, dose-limiting toxicity name",
    "Grade, int/string, CTCAE grading",
    "At_Level, int/string, dose level of event",
    "Observed_Frequency, int/string, count of patients with this DLT",
    "Total, int/string, total patients at this level"
]

TREATMENT_PROMPT_ADDITION = """
    SPECIAL INSTRUCTION FOR SAFETY DATA:
    The output for these fields must be grouped by event. 
    Instead of independent fields, return a list of "Toxicities" where each object contains:
    {
        "DLT": "...",
        "Grade": "...",
        "At_Level": "...",
        "Frequency": "...",
        "Total_Patients": "..."
    }
"""