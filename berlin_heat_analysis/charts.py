import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, spearmanr

# ---------------------------------------
# Load your CSV files
# ---------------------------------------
temp_df = pd.read_csv(
    r"H:/BHT/urban technology/urban_project/CSV/berlin_mean_temperature_by_area.csv"
)

green_df = pd.read_csv(
    r"H:/BHT/urban technology/urban_project/CSV/berlin_green_coverage.csv"
)

# ---------------------------------------
# Merge them on area
# ---------------------------------------
df = pd.merge(temp_df, green_df, on="area", how="inner")

print("\nMERGED DATAFRAME:")
print(df.head())

# ---------------------------------------
# Prepare groups for T-test
# ---------------------------------------
median_green = df["green_area"].median()

low_green = df[df["green_area"] < median_green]
high_green = df[df["green_area"] >= median_green]

# ---------------------------------------
# Run T-test
# ---------------------------------------
t_stat, p_val_ttest = ttest_ind(
    low_green["mean_temp_c"],
    high_green["mean_temp_c"],
    equal_var=False
)

print("\nT-TEST RESULTS")
print("---------------------")
print("t-statistic =", round(t_stat, 4))
print("p-value     =", p_val_ttest)

# ---------------------------------------
# Run Spearman correlation
# ---------------------------------------
rho, p_val_spear = spearmanr(df["green_area"], df["mean_temp_c"])

print("\nSPEARMAN CORRELATION RESULTS")
print("----------------------------")
print("rho     =", round(rho, 4))
print("p-value =", p_val_spear)

# =====================================================
#       📊 1. BOX PLOT (T-TEST VISUALIZATION)
# =====================================================
plt.figure(figsize=(7, 5))
plt.boxplot(
    [low_green["mean_temp_c"], high_green["mean_temp_c"]],
    labels=["Low Green Areas", "High Green Areas"]
)
plt.ylabel("Mean Temperature (°C)")
plt.title("Temperature Difference Between Low & High Green Areas")
plt.grid(True)
plt.tight_layout()
plt.savefig("boxplot_temperature_green.png", dpi=300)
plt.show()

# =====================================================
#   📈 2. SCATTER PLOT (CORRELATION VISUALIZATION)
# =====================================================
plt.figure(figsize=(7, 5))
plt.scatter(df["green_area"], df["mean_temp_c"])

# Trendline
z = np.polyfit(df["green_area"], df["mean_temp_c"], 1)
p = np.poly1d(z)
plt.plot(df["green_area"], p(df["green_area"]))

plt.xlabel("Green Coverage (0–1)")
plt.ylabel("Mean Temperature (°C)")
plt.title("Correlation: Green Coverage vs Temperature")
plt.grid(True)
plt.tight_layout()
plt.savefig("scatter_green_vs_temp.png", dpi=300)
plt.show()

# =====================================================
#   📊 3. HISTOGRAM (DISTRIBUTION COMPARISON)
# =====================================================
plt.figure(figsize=(7, 5))
plt.hist(low_green["mean_temp_c"], alpha=0.7, label="Low Green", bins=10)
plt.hist(high_green["mean_temp_c"], alpha=0.7, label="High Green", bins=10)
plt.legend()
plt.xlabel("Mean Temperature (°C)")
plt.ylabel("Frequency")
plt.title("Temperature Distribution: Low vs High Green Coverage")
plt.grid(True)
plt.tight_layout()
plt.savefig("histogram_temperature_distribution.png", dpi=300)
plt.show()
