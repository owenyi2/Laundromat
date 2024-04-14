import numpy as np
import jsonpickle
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("parse/merged_data.csv", index_col = 0)
print(df)

midprice = df["mid_price"]
print(midprice)

# Defaults were emaLength = 20, emaGainLimit = 50, hullPeriod = 7

emaLength = 40
emaGainLimit = 50
hullPeriod = 14

halfHullPeriod = int(round(hullPeriod * 0.5))
rootHullPeriod = int(round(hullPeriod ** 0.5))

price_cache = []
raw_hma_cache = []

alpha = 2.0 / (emaLength + 1)

ema_previous = midprice.values[0]
ec_previous = midprice.values[0]

EC = []
HMA = []
DMA = []

# dma_cache = []
# dma_lookback = 50
# 
# POLY_SLOPE =  []
# POLY_CONC = []

def wma(data_cache):
    data = np.array(data_cache)
    weights = np.arange(len(data)) + 1

    return np.dot(data, weights) / weights.sum()

for p in midprice:  
    price_cache.append(p)
    price_cache = price_cache[-hullPeriod:]
    
    wma1 = wma(price_cache[-halfHullPeriod:])
    wma2 = wma(price_cache[-hullPeriod:])
    raw_hma = (2*wma1) - wma2

    raw_hma_cache.append(raw_hma)
    raw_hma_cache = raw_hma_cache[-rootHullPeriod:]
    hma = wma(raw_hma_cache)

    HMA.append(hma)

    ema = alpha * p + (1-alpha) * ema_previous 
    leastError = float("inf")

    for value1 in range(-emaGainLimit, emaGainLimit + 1):
        gain = value1 / 10
        ec = alpha * (ema + gain*(p - ec_previous)) + (1- alpha) * ec_previous

        error = p - ec
        if abs(error) < leastError:
            leastError = abs(error)
            bestGain = gain

    ec = alpha * (ema + bestGain * (p - ec_previous)) + (1-alpha) * ec_previous
    EC.append(ec)

    ema_previous = ema
    ec_previous = ec
    
    dma = (ec + hma) * 0.5

    DMA.append(int(round(dma)))

    # dma_cache.append(dma)
    # dma_cache = dma_cache[-dma_lookback:]

    # if len(dma_cache) == dma_lookback:
    #     t = np.arange(-dma_lookback, 0, 1) + 1 # latest is centered at 0
    #     weights = np.sqrt(np.arange(dma_lookback) + 1)
    #     coeffs = np.polyfit(t, np.array(dma_cache), deg = 2, w=weights)
    #     
    #     POLY_SLOPE.append(coeffs[1])
    #     POLY_CONC.append(coeffs[0] / 2)
    # else:
    #     POLY_SLOPE.append(np.nan)
    #     POLY_CONC.append(np.nan)

EC = np.array(EC)
HMA = np.array(HMA)
DMA = np.array(DMA)
# POLY_SLOPE = np.array(POLY_SLOPE)
# POLY_CONC = np.array(POLY_CONC)

fig, ax = plt.subplots(1, 1)


ax.plot(midprice.values)
# plt.plot(EC)
# plt.plot(HMA)
ax.plot(DMA)

# twin = ax.twinx()
# twin.plot(POLY_SLOPE, color="tab:red")
# twin.plot(np.zeros_like(POLY_SLOPE))
plt.show()
