from copy import deepcopy
import numpy as np
import jsonpickle
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("parse/merged_data.csv", index_col = 0)
print(df)
data_bottle = pd.read_csv("round-2-island-data-bottle/prices_round_2_day_1.csv", sep=";")

fig, ax = plt.subplots(1, 1, figsize=(10, 6))

dom_ewma = df["bid_price_1"].ewm(span=10).mean()
dom_ewms = df["bid_price_1"].ewm(span=10).std()

real_int_ask = 0.75+data_bottle["ORCHIDS"] + data_bottle["IMPORT_TARIFF"]+data_bottle["TRANSPORT_FEES"]
int_ewma = real_int_ask.ewm(span=50).mean()
int_ewms = real_int_ask.ewm(span=50).std()
signal_ewma = real_int_ask.ewm(span = 100).mean()

ax.plot(df["bid_price_1"], label = "dom. bid")
ax.plot(dom_ewma - dom_ewms, color="navy", alpha = 0.5)
ax.plot(dom_ewma + dom_ewms, color="navy", alpha = 0.5)

ax.plot(real_int_ask, label="real int. ask")
ax.plot(int_ewma - int_ewms, color="chocolate", alpha = 0.5)
ax.plot(int_ewma, color="chocolate", alpha = 0.5)
ax.plot(int_ewma + int_ewms, color="chocolate", alpha = 0.5)
ax.plot(signal_ewma, color="red", alpha = 0.5)


ax.legend(loc="best")

plt.show()

# ===
# dom_bid_array = []
# dom_ewma_array = []
# dom_ewms_array = []
# int_ask_array = []
# int_ewma_array = []
# int_ewms_array = []
# 
# dom_alpha = 2.0 / (10+1)
# int_alpha = 2.0 / (50+1)
# 
# for idx, row in df.iterrows():
#     dom_bid = row["bid_price_1"]
#     int_ask = row["askPrice"] + row["importTariff"] + row["transportFee"]
# 
#     if len(dom_bid_array) == 0:
#         dom_bid_array.append(dom_bid)
#         dom_ewma_array.append(dom_bid)
#         dom_ewms_array.append(0)
#         int_ask_array.append(int_ask)
#         int_ewma_array.append(int_ask)
#         int_ewms_array.append(0)
#         continue
# 
#     dom_ewma_array.append(dom_alpha * dom_bid + (1-dom_alpha) * dom_bid_array[-1])
#     int_ewma_array.append(int_alpha * int_ask + (1-int_alpha) * int_ask_array[-1])
# 
#     dom_ewms = ((1-dom_alpha)*(dom_ewms_array[-1]**2 + dom_alpha*(dom_bid - dom_ewma_array[-1])**2))**0.5
#     int_ewms = ((1-int_alpha)*(int_ewms_array[-1]**2 + int_alpha*(int_ask - int_ewma_array[-1])**2))**0.5
#     dom_ewms_array.append(dom_ewms)
#     int_ewms_array.append(int_ewms)
# 
#     dom_bid_array.append(dom_bid)
#     int_ask_array.append(int_ask)
# 
# dom_bid_array = np.array(dom_bid_array)
# dom_ewma_array = np.array(dom_ewma_array)
# dom_ewms_array = np.array(dom_ewms_array)
# int_ask_array = np.array(int_ask_array)
# int_ewma_array = np.array(int_ewma_array)
# int_ewms_array = np.array(int_ewms_array)
# 
# breakpoint()
# 
# ax.plot(dom_bid_array, label = "dom. bid")
# ax.plot(dom_ewma_array - dom_ewms_array, color="navy", alpha = 0.5)
# ax.plot(dom_ewma_array + dom_ewms_array, color="navy", alpha = 0.5)
# 
# ax.plot(int_ask_array, label="real int. ask")
# ax.plot(int_ewma_array - int_ewms_array, color="chocolate", alpha = 0.5)
# ax.plot(int_ewma_array + int_ewms_array, color="chocolate", alpha = 0.5)
# 
# ax.legend(loc="best")
# 
# plt.show()
# use this https://stackoverflow.com/questions/40754262/pandas-ewm-std-calculation
# for implementation
