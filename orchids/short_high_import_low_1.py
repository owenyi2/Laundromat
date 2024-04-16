from copy import deepcopy
import numpy as np
import jsonpickle
import pandas as pd
import matplotlib.pyplot as plt

data_bottle = pd.read_csv("round-2-island-data-bottle/prices_round_2_day_1.csv", sep=";")

fig, ax = plt.subplots(2, 1, figsize=(10, 6))

EWMA_SPAN = 50
ROLLING = 20

real_int_ask = 0.75+data_bottle["ORCHIDS"] + data_bottle["IMPORT_TARIFF"]+data_bottle["TRANSPORT_FEES"]

int_ewma = real_int_ask.ewm(span=EWMA_SPAN).mean()

delta = real_int_ask - int_ewma 
rolling_min = delta.rolling(ROLLING).min()
rolling_max = delta.rolling(ROLLING).max()


ax[0].plot(real_int_ask)
ax[1].plot(delta)
ax[1].plot(rolling_min)
ax[1].plot(rolling_max)
# ax[2].plot((delta - rolling_min) / (rolling_max - rolling_min))
# 
# x_min = 500
# x_max = 600
# for a in ax:
#     a.set_xlim([x_min, x_max])
# ax[0].set_ylim([real_int_ask[x_min:x_max].min() - 1, real_int_ask[x_min:x_max].max() + 1])
# ax[1].set_ylim([delta[x_min:x_max].min() - 1, delta[x_min:x_max].max() + 1])

plt.show()

