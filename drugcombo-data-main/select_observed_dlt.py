import pandas as pd

# 加载原始 observed_dlt 文件
df = pd.read_csv("observed_dlt.csv")

# 筛选所需的列
columns_to_keep = [
    "PMID",
    "DLT",
    "Grade",
    "At_Level",  # 注意：有时为 At_level，根据你的实际列名大小写
    "Observed_Frequency",
    "Total",
    "combined_dose_info"
]

# 自动处理大小写可能不同的问题
df.columns = [col.strip() for col in df.columns]
columns_to_keep = [col for col in columns_to_keep if col in df.columns]

# 保留并导出
df_filtered = df[columns_to_keep]
df_filtered.to_csv("observed_dlt_extraction.csv", index=False)
print("[✓] Saved observed_dlt_extraction.csv")
