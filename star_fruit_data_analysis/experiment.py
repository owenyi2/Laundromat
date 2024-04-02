import re 
import json
import numpy as np
import pprint
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression


LOG_FILE = "f65e7e67-4d41-4642-89ac-294c9c27cbd2_1.log"

regex = re.findall("URMOM(.*?)URDAD", open(LOG_FILE).read())
regex = [r.replace("\\", "") for r in regex]

data = [json.loads(r) for r in regex]

ITEM = "STARFRUIT"

best_bids = []
best_asks = []

for d in data:
    bids = d["order_depths"][ITEM].get("buy_orders", dict())
    asks = d["order_depths"][ITEM].get("sell_orders", dict())

    best_bids.append(max([int(p) for p in bids.keys()])) 
    best_asks.append(min([int(p) for p in asks.keys()])) 

best_bids = np.array(best_bids[:2000:2])
best_asks = np.array(best_asks[:2000:2])

mid_price = pd.Series((best_bids + best_asks) / 2.0)

m = mid_price.rolling(50).apply(lambda x: LinearRegression().fit(np.array(x.index).reshape(-1, 1), x).predict(np.array(x.index[-1]+10).reshape(-1, 1)))


fig, ax = plt.subplots(2,2, figsize=(14, 8))

ax[0, 0].plot(pd.Series(best_bids), label="bids")
ax[1, 0].plot(pd.Series(best_bids) / pd.Series(best_bids).shift(1), label="bids[i] / bids[i-1]")
ax[0, 1].plot(pd.Series(best_asks), label="asks")
ax[1, 1].plot(pd.Series(best_asks) / pd.Series(best_asks).shift(1), label="asks[i] / asks[i-1]")

# ax.plot(best_bids)
# ax.plot(best_asks)
# ax.plot(mid_price)

# ax.plot(m)
plt.show()
plt.savefig("yeet.png")

