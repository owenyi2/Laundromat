import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# sunlight needs to be above threshold <https://youtu.be/k4mV5XZZM-I?t=95>
# whenever sunlight exposure is less than 7 hours a day, production will decrease 4% for every 10minutes
# humidity needs to be between 60% and 80%
# outside these limits production will fall 2% for every 5% point of humidity change

dfs = []
for i in range(-1, 2):
    file_name = f"round-2-island-data-bottle/prices_round_2_day_{i}.csv"
    df = pd.read_csv(file_name, index_col = 0, sep=";")
    dfs.append(df)

fig = plt.figure(figsize=(15, 6))

for i in range(-1, 2):
    file_name = f"round-2-island-data-bottle/prices_round_2_day_{i}.csv"
    df = pd.read_csv(file_name, index_col = 0, sep=";")
    dfs.append(df)

    ax = fig.add_subplot(2, 3, i+2)
    ax1 = fig.addsubplot(2, 3, i+2)
    twin1 = ax.twinx()
    twin2 = ax.twinx()

    ax.plot(df["ORCHIDS"].diff())
    twin1.plot(df["HUMIDITY"])
    twin2.plot(df["SUNLIGHT"])



 
plt.show()

