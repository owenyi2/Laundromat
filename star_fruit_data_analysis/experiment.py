import re 
import json
import numpy as np
import pprint
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression

df = pd.read_csv("activity.csv", sep=";")
df = df[df["product"] == "STARFRUIT"]

mid_price = df["mid_price"]
best_bid = df["bid_price_1"]
best_ask = df["ask_price_1"]

bid_returns = best_bid - best_bid.shift(1)
ask_returns = best_ask - best_ask.shift(1)

n = 2

bid_sigma_left = np.mean(bid_returns) - np.std(bid_returns) * n
bid_sigma_right = np.mean(bid_returns) + np.std(bid_returns) * n

ask_sigma_left = np.mean(ask_returns) - np.std(ask_returns) * n
ask_sigma_right = np.mean(ask_returns) + np.std(ask_returns) * n

fig, ax = plt.subplots(2, 2, figsize=(12, 6))

ax[0, 0].set_title("bid")
ax[0, 0].hist(bid_returns, bins=30)
ax[0, 0].axvline(bid_sigma_left, color="black")
ax[0, 0].axvline(bid_sigma_right, color="black")
ax[1, 0].plot(bid_returns)
ax[1, 0].axhline(bid_sigma_left, color="black")
ax[1, 0].axhline(bid_sigma_right, color="black")

ax[0, 1].set_title("ask")
ax[0, 1].hist(ask_returns, bins=30)
ax[0, 1].axvline(ask_sigma_left, color="black")
ax[0, 1].axvline(ask_sigma_right, color="black")
ax[1, 1].plot(ask_returns)
ax[1, 1].axhline(ask_sigma_left, color="black")
ax[1, 1].axhline(ask_sigma_right, color="black")

plt.show()
