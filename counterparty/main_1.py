import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

day = 2

round_3_trades_file = f"round-5-island-data-bottle/trades_round_3_day_{day}_wn.csv"
round_3_prices_file = f"round-3-island-data-bottle/prices_round_3_day_{day}.csv"

snakes = ["Remy", "Rhianna", "Ruby", "Vinnie", "Vladimir"]
products = ["ROSES", "CHOCOLATE", "STRAWBERRIES", "GIFT_BASKET"]

t_df = pd.read_csv(round_3_trades_file, sep=";")
p_df = pd.read_csv(round_3_prices_file, sep=";")

trader = ""
product = "CHOCOLATE"

t_df = t_df[((t_df["buyer"] == trader ) | (t_df["seller"] == trader)) & (t_df["symbol"] == product)]
t_df["side"] = np.where(t_df["buyer"] == trader, 1, -1)

# t_df["position"] = np.cumsum(t_df["side"] * t_df["quantity"])
t_df["position"] = np.cumsum(t_df["side"])

print(t_df)

fig, ax = plt.subplots(2, 1)

ax[0].plot(t_df["timestamp"], t_df["position"])
ax[1].plot(p_df[p_df["product"]==product]["timestamp"], p_df[p_df["product"] == product]["mid_price"])
plt.show()
