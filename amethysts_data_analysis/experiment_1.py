import re 
import json
import numpy as np
import pprint
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("activity.csv", sep=";", skiprows=1)

amethyst_df = df[df["product"] == "AMETHYSTS"]

fig, ax = plt.subplots(figsize=(10, 7))

ax.plot(amethyst_df["bid_price_1"], color="cyan", marker="+")
ax.plot(amethyst_df["bid_price_2"], color="blue", marker="+")
ax.plot(amethyst_df["bid_price_3"], color="midnightblue", marker="+")

ax.plot(amethyst_df["ask_price_1"], color="orange", marker="+")
ax.plot(amethyst_df["ask_price_2"], color="red", marker="+")
ax.plot(amethyst_df["ask_price_3"], color="maroon", marker="+")

ax.set_xlim(0, 800)
fig.savefig("yeet.png")
plt.show()
