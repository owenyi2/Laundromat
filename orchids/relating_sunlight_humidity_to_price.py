import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# sunlight needs to be above threshold <https://youtu.be/k4mV5XZZM-I?t=95>
# whenever sunlight exposure is less than 7 hours a day, production will decrease 4% for every 10minutes
# humidity needs to be between 60% and 80%
# outside these limits production will fall 2% for every 5% point of humidity change
from sklearn.linear_model import LinearRegression

dfs = []
for i in range(-1, 2):
    file_name = f"round-2-island-data-bottle/prices_round_2_day_{i}.csv"
    df = pd.read_csv(file_name, index_col = 0, sep=";")
    dfs.append(df)

fig = plt.figure(figsize=(15, 6))

ax_all = fig.add_subplot(1, 5, 4)

for i in range(-1, 2):
    file_name = f"round-2-island-data-bottle/prices_round_2_day_{i}.csv"
    df = pd.read_csv(file_name, index_col = 0, sep=";")
    dfs.append(df)

    X = df[["HUMIDITY", "SUNLIGHT"]]
    y = df["ORCHIDS"]
    ax = fig.add_subplot(1, 5, i+2)
    ax.scatter(X["HUMIDITY"].diff(), X["SUNLIGHT"].rolling(10).mean(), c = y, cmap="bwr")
    ax.annotate("beginning", (X["HUMIDITY"].values[0], X["SUNLIGHT"].values[0]), color="xkcd:yellow")
    ax.annotate("end", (X["HUMIDITY"].values[-1], X["SUNLIGHT"].values[-1]), color="xkcd:yellow")
    ax.set_xlabel("HUMIDITY")
    ax.set_ylabel("SUNLIGHT")
    ax.set_facecolor("black")

    ax_all.scatter(X["HUMIDITY"].diff(), X["SUNLIGHT"].cumsum(), c = y, cmap="bwr")

df = pd.concat(dfs)
X = df[["HUMIDITY", "SUNLIGHT"]]
y = df["ORCHIDS"]

# ax.scatter(X["HUMIDITY"], X["SUNLIGHT"], c = y, cmap="bwr")
ax_all.set_xlabel("HUMIDITY")
ax_all.set_ylabel("SUNLIGHT")
ax_all.set_facecolor("black")

ax1 = fig.add_subplot(1, 5, 5, projection='3d')
ax1.scatter(df["HUMIDITY"], df["SUNLIGHT"], df["ORCHIDS"], marker="*")
ax1.set_xlabel('HUMIDITY')
ax1.set_ylabel('SUNLIGHT')
ax1.set_zlabel('ORCHIDS')
 
plt.show()


