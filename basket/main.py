import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

dfs = []

for i in range(3):
    filename = f"round-3-island-data-bottle/prices_round_3_day_{i}.csv"
    dfs.append(pd.read_csv(filename, sep=";"))

df = dfs[1].iloc[:1000]
chocolate_midprice = df[df["product"] == "CHOCOLATE"]["mid_price"].reset_index(drop=True)
giftbasket_midprice = df[df["product"] == "GIFT_BASKET"]["mid_price"].reset_index(drop=True)
roses_midprice = df[df["product"] == "ROSES"]["mid_price"].reset_index(drop=True)
strawberries_midprice = df[df["product"] == "STRAWBERRIES"]["mid_price"].reset_index(drop=True)

synthetic_price = 4 * chocolate_midprice + 6 * strawberries_midprice + roses_midprice

premia = synthetic_price - giftbasket_midprice
premia_mean, premia_std = premia.mean(), premia.std()

print(premia_mean, premia_std)

fig, ax = plt.subplots(1, 1)

ax.plot(giftbasket_midprice - synthetic_price)
ax.plot((giftbasket_midprice - synthetic_price).ewm(span=20).mean())
plt.show()

premia = np.array([])

for df in dfs:
    chocolate_midprice = df[df["product"] == "CHOCOLATE"]["mid_price"].values
    giftbasket_midprice = df[df["product"] == "GIFT_BASKET"]["mid_price"].values
    roses_midprice = df[df["product"] == "ROSES"]["mid_price"].values
    strawberries_midprice = df[df["product"] == "STRAWBERRIES"]["mid_price"].values
    
    synthetic_price = 4 * chocolate_midprice + 6 * strawberries_midprice + roses_midprice
    p = synthetic_price - giftbasket_midprice

    premia = np.concatenate((premia, p))

print(premia.mean(), premia.std())
plt.show()
