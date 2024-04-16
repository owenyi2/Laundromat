from copy import deepcopy
import numpy as np
import jsonpickle
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("round-2-island-data-bottle/prices_round_2_day_1.csv", sep=";")

fig, ax = plt.subplots(2, 1)

price = df["ORCHIDS"]
ema = price.ewm(span=1000).mean()

ax[0].plot(price)
ax[0].plot(ema)

ax[1].plot(ema > price)
plt.show()
