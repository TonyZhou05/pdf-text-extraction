import pandas as pd
import re

# Set file names
gold_file = "drugcombo-data-main/observed_dlt_extraction.csv"  # Ground truth labels
pred_file = "results.csv"  # Model predictions

# Set columns (order does not matter, as long as the contents are consistent)
columns = [
    "PMID",
    "DLT",
    "Grade",
    "At_Level",
    "Observed_Frequency",
    "Total",
    "combined_dose_info",
]

# Read data (note the delimiter, assuming tab-delimited here)
df_gold = pd.read_csv(gold_file, names=columns)[1:]
df_pred = pd.read_csv(pred_file, names=columns)[1:]

PMID_set = set(df_pred["PMID"])
df_gold = df_gold[df_gold["PMID"].isin(PMID_set)]

# You can decide whether to use all fields or only partial fields for evaluation:
# match_fields = ["PMID", "DLT", "Grade", "At_Level", "combined_dose_info"]
match_fields = [
    "PMID",
    "DLT",
    "Grade",
    "At_Level",
    "Observed_Frequency",
    "Total",
    "combined_dose_info",
]

# Define fields that should be converted to integers
# int_fields = ["Grade", "At_Level", "Observed_Frequency", "Total"]
int_fields = []


def extract_number(value):
    """Try to extract numbers from a string"""
    numbers = re.findall(r"\d+", value)
    if numbers:
        return int(numbers[0])
    else:
        return ""


# Preprocessing function
def preprocess_row(row):
    processed = []
    for field in match_fields:
        value = row[field]
        if pd.isna(value):
            value = ""
        value = str(value).strip()
        if field in int_fields:
            try:
                value = int(float(value))
            except:
                value = extract_number(value)
        processed.append(value)
    return tuple(processed)


# Generate sets
gold_set = set(preprocess_row(row) for _, row in df_gold.iterrows())
pred_set = set(preprocess_row(row) for _, row in df_pred.iterrows())

for temp in PMID_set:
    print(temp)
    print("     gold_set:")
    for gold in gold_set:
        if temp in gold:
            print("     ", gold)
    print("     pred_set:")
    for pred in pred_set:
        if temp in pred:
            print("     ", pred)

# Compute evaluation metrics
tp = len(gold_set & pred_set)  # Correct predictions
fp = len(pred_set - gold_set)  # Over-predicted
fn = len(gold_set - pred_set)  # Missed predictions

# Precision, Recall, F1
precision = tp / len(pred_set) if pred_set else 0
recall = tp / len(gold_set) if gold_set else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

# Print results
print(f"Total gold samples: {len(gold_set)}")
print(f"Total predicted samples: {len(pred_set)}")
print(f"True Positives (TP): {tp}")
print(f"False Positives (FP): {fp}")
print(f"Precision: {precision:.3f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
