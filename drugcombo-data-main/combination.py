import pandas as pd
import chardet
import os

def clean_and_read_csv(path, tmp_path="__cleaned_tmp.csv"):
    """
    自动检测编码 → 忽略非法字符 → 转为 UTF-8 → 读取为 Pandas DataFrame
    """
    print(f"[INFO] Reading: {path}")

    # 检测原始文件编码
    with open(path, 'rb') as f:
        raw_data = f.read(100000)  # 前10万字节足够判断
        detected = chardet.detect(raw_data)
        encoding = detected['encoding'] or 'ISO-8859-1'
        print(f"[INFO] Detected encoding for {path}: {encoding}")

    # 清洗并保存为 utf-8 中间文件
    with open(path, 'r', encoding=encoding, errors='ignore') as f_in, \
         open(tmp_path, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            f_out.write(line)

    # 用 pandas 读取中间文件
    df = pd.read_csv(tmp_path)
    os.remove(tmp_path)  # 清理临时文件
    return df

# === Step 1: 加载所有数据 ===
trial = clean_and_read_csv("trial.csv")
drug = clean_and_read_csv("drug.csv")
schema = clean_and_read_csv("schema.csv")
dlt_def = clean_and_read_csv("dlt_definition.csv")
dose_level = clean_and_read_csv("dose_level.csv")
mtd = clean_and_read_csv("mtd.csv")
obs_dlt = clean_and_read_csv("observed_dlt.csv")

# === Step 2: 预处理 observed_dlt 的字段名（At_level → Dose_Level） ===
obs_dlt = obs_dlt.rename(columns={"At_Level": "Dose_Level"})

print("[DEBUG] Columns in observed_dlt:", obs_dlt.columns.tolist())

# === Step 3: 合并数据集 ===
print("[INFO] Merging data...")

# Step: 合并 trial + schema + drug + dlt_def
df = trial.merge(schema, on=["PMID", "NCTID"], how="left")
df = df.merge(drug, on=["PMID", "NCTID"], how="left")
df = df.merge(dlt_def, on=["PMID", "NCTID", "CombnID"], how="left")

# Step: obs_dlt + dose_level
obs_dlt_full = obs_dlt.merge(dose_level, on=["PMID", "NCTID", "CombnID", "Dose_Level"], how="left")

# Step: 合并 obs_dlt_full 到主表（不要再用 Dose_Level）
df = df.merge(obs_dlt_full, on=["PMID", "NCTID", "CombnID"], how="left")

# Step: 合并 mtd
df = df.merge(mtd, on=["NCTID", "CombnID"], how="left")


# === Step 4: 保存结果 ===
output_path = "combined_trial_dataset.csv"
df.to_csv(output_path, index=False)
print(f"[✓] Combined dataset saved to: {output_path}")
