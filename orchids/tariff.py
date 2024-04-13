import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("parse/merged_data.csv", index_col = 0)

df["bid_price_1"] - df["bidPrice"] 

print(df[["bidPrice", "askPrice", "bid_price_1", "ask_price_1"]])

fig, ax = plt.subplots(4, 1, figsize=(10, 7))

ax[0].plot(df["bid_price_1"], label="domestic bid")
ax[0].plot(df["bidPrice"], label="international bid")

ax[0].plot(df["ask_price_1"], label="domestic ask")
ax[0].plot(df["askPrice"], label="international ask")

ax[0].legend(loc="best")

# ax[1].plot(df["bid_price_1"] - df["bidPrice"], label = "Bid: domestic - international")
# ax[1].plot(df["ask_price_1"] - df["askPrice"], label = "Ask: domestic - international")
# ax[1].legend(loc="best")

ax[1].plot(df["bid_price_1"] - df["askPrice"], label = "Domestic bid - Internatial ask")
ax[1].plot(df["ask_price_1"] - df["bidPrice"], label = "Domestic ask- Internatial bid")
ax[1].legend(loc="best")

ax[2].plot(df["transportFee"], label="transportFee")
ax[2].plot(df["exportTariff"], label="exportTariff")
ax[2].plot(df["importTariff"], label="importTariff")
ax[2].legend(loc="best")

ax[3].plot(df["bid_price_1"], label="domestic bid")
ax[3].plot(df["bidPrice"] - df["exportTariff"] - df["transportFee"], label="real international bid")

ax[3].plot(df["ask_price_1"], label="domestic ask")
ax[3].plot(df["askPrice"] + df["importTariff"] + df["transportFee"], label="real international ask")

ax[3].legend(loc="best")
plt.show()


