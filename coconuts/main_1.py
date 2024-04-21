import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.stattools import adfuller

dfs = []
for day in range(1, 4):
    file_name = f"round-4-island-data-bottle/prices_round_4_day_{day}.csv"
    df = pd.read_csv(file_name, index_col = 0, sep=";")
    dfs.append(df)

df = pd.concat(dfs)


coconut_df = df[df["product"] == "COCONUT"].reset_index(drop=True)
coupon_df = df[df["product"] == "COCONUT_COUPON"].reset_index(drop=True)

coconut = coconut_df["mid_price"] 
coupon = coupon_df["mid_price"] 

A = np.vstack([coconut, np.ones(len(coconut))]).T
m, c = np.linalg.lstsq(A, coupon, rcond=None)[0]

m = 0.5

adftest = adfuller(coupon - m * coconut, autolag='AIC', regression='ct')
print("ADF Test Results")
print("Null Hypothesis: The series has a unit root (non-stationary)")
print("ADF-Statistic:", adftest[0])
print("P-Value:", adftest[1])
print("Number of lags:", adftest[2])
print("Number of observations:", adftest[3])
print("Critical Values:", adftest[4])
print("Note: If P-Value is smaller than 0.05, we reject the null hypothesis and the series is stationary")

fig, ax = plt.subplots(1, 1)

print(m)

stat = coconut - 2 * coupon

print(stat.mean(), stat.std())

        # synthetic_price = midprice["COCONUT"] - 2 * midprice["COCONUT_COUPON"] 
        # z_score = (synthetic_price - (-4364.904)) / 13.384 

ax.plot(stat - stat.mean())
ax.plot(stat - stat.expanding().mean())
plt.show()
