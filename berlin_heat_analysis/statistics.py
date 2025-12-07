import pandas as pd
from scipy.stats import ttest_ind, spearmanr

# -------------------------
# Load datasets
# -------------------------
temp_path = "H:/BHT/urban technology/urban_project/CSV/berlin_mean_temperature_by_area.csv"
green_path = "H:/BHT/urban technology/urban_project/CSV/berlin_green_coverage.csv"

df_temp = pd.read_csv(temp_path)
df_green = pd.read_csv(green_path)

# -------------------------
# Check expected columns exist
# -------------------------
required_temp_cols = {"area", "mean_temp_c"}
required_green_cols = {"area", "green_area"}

if not required_temp_cols.issubset(df_temp.columns):
    raise ValueError("Temperature CSV must contain: 'area', 'mean_temp_c'")

if not required_green_cols.issubset(df_green.columns):
    raise ValueError("Green coverage CSV must contain: 'area', 'green_area'")

# -------------------------
# Merge datasets
# -------------------------
df = pd.merge(df_temp, df_green, on="area", how="inner")

print("Merged dataset preview:")
print(df.head())

# -------------------------
# 1. T-test for temperature differences
#    (Low green vs high green)
# -------------------------
median_green = df["green_area"].median()

low_green = df[df["green_area"] < median_green]["mean_temp_c"]
high_green = df[df["green_area"] >= median_green]["mean_temp_c"]

t_stat, p_val_t = ttest_ind(low_green, high_green, equal_var=False)

# -------------------------
# 2. Spearman correlation
# -------------------------
rho, p_val_corr = spearmanr(df["green_area"], df["mean_temp_c"])

# -------------------------
# Print results
# -------------------------
print("\n--------------------------------------")
print("          STATISTICAL RESULTS         ")
print("--------------------------------------\n")

print("T-TEST (Temperature: Low vs High Green Areas)")
print(f"t-statistic = {t_stat:.3f}")
print(f"p-value     = {p_val_t:.6f}")

print("\nSpearman CORRELATION (Green Coverage vs Temperature)")
print(f"rho         = {rho:.3f}")
print(f"p-value     = {p_val_corr:.6f}")

# -------------------------
# Interpretation for slide
# -------------------------
print("\n--------------------------------------")
print("           INTERPRETATION             ")
print("--------------------------------------\n")

if p_val_t < 0.05:
    print("✔ Low-green areas are significantly hotter than high-green areas.")
else:
    print("✖ Temperature difference between low and high green areas is NOT statistically significant.")

if p_val_corr < 0.05:
    trend = "negative" if rho < 0 else "positive"
    print(f"✔ Significant {trend} correlation: green coverage relates to temperature.")
else:
    print("✖ No statistically significant correlation between green coverage and temperature.")

print("\n--------------------------------------")
