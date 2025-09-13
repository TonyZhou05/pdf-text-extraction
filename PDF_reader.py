import os
import fitz  # PyMuPDF
import json
import pandas as pd
import re
from openai import AzureOpenAI

# === Azure OpenAI Configuration ===
AZURE_OPENAI_ENDPOINT = os.getenv("ENDPOINT_URL")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv(
    "DEPLOYMENT_NAME", "gpt-4o"
)  # Replace with your deployment name
AZURE_OPENAI_API_VERSION = (
    "2024-02-15-preview"  # Or the version supported by your resource
)

# === Initialize AzureOpenAI Client ===
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)

# === Directory Settings ===
PDF_FOLDER = "pdfs"
RESULT_FOLDER = "results"
os.makedirs(RESULT_FOLDER, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print(f"[INFO] Extracting text from PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    return "".join([page.get_text() for page in doc])


def extract_dlt_info_with_gpt(pdf_text):
    """Extract DLT-related structured data using Azure GPT-4."""
    print("[INFO] Calling Azure GPT-4 API...")
    prompt = f"""
You are an expert assistant helping extract clinical trial toxicity data.

Extract all reported dose-limiting toxicities (DLTs) from the following clinical trial text.
For each DLT, extract the following fields:
- DLT name: The DLT occured on the participants.
- Grade: The severity of the DLT.
- At_level: The dose the participants take for the DLT.
- Observed Frequency: How many participants have the DLT.
- Total: The total number of participants at the sepcific dose.
- Combined dose info: List all drugs and their doses that the participant received at the time the DLT occurred. Keep all components, including repeated drugs with different doses. Preserve the order and original formatting as in the publication, e.g., "seribantumab (20 mg/kg), cetuximab (400 mg/m2), cetuximab (250 mg/m2), irinotecan (180 mg/m2)".

Output the result in JSON format like:
[
  {{
    "DLT": "diarrhea",
    "Grade": "3",
    "At_Level": "2",
    "Observed_Frequency": "1",
    "Total": "6",
    "combined_dose_info": "cetuximab (250 mg/m2), lumretuzumab (800 mg)"
  }}
]

Text:
\"\"\"
{pdf_text}
\"\"\"
"""
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful clinical trial information extractor.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def save_json_and_excel(data, pmid):
    """Save the extracted JSON and Excel file."""
    json_path = os.path.join(RESULT_FOLDER, f"{pmid}.json")
    excel_path = os.path.join(RESULT_FOLDER, f"{pmid}.xlsx")

    # Try parsing JSON
    try:
        # Step 1: Extract JSON block inside markdown, if any
        match = re.search(r"```(?:json)?\s*(\[\s*{.*?}\s*\])\s*```", data, re.DOTALL)
        if match:
            cleaned = match.group(1)
        else:
            cleaned = data.strip().strip("```").strip()

        # Step 2: Parse as JSON
        parsed_data = json.loads(cleaned)

    except json.JSONDecodeError:
        print(f"[✗] GPT output not valid JSON for {pmid}. Saving raw output.")
        parsed_data = {"raw_output": data}

    # Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)

    # Save Excel if possible
    if isinstance(parsed_data, list):
        df = pd.DataFrame(parsed_data)
        df.insert(0, "PMID", pmid)
        df.to_excel(excel_path, index=False)
        print(f"[✓] Saved: {excel_path}")
    else:
        print(f"[✗] No structured data to save as Excel for {pmid}.")


def process_all_pdfs():
    """Main loop for processing all PDF files."""
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    print(f"[INFO] Found {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files:
        pmid = os.path.splitext(pdf_file)[0]
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)

        try:
            text = extract_text_from_pdf(pdf_path)
            gpt_output = extract_dlt_info_with_gpt(text)
            save_json_and_excel(gpt_output, pmid)
        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_file}: {e}")
            with open("error_log.txt", "a") as f:
                f.write(f"{pdf_file}: {e}\n")


if __name__ == "__main__":
    process_all_pdfs()
