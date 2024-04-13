import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp

file_name = "round-2-island-data-bottle/prices_round_2_day_-1.csv"

df = pd.read_csv(file_name, sep=";")

print(df)

sunlight = df["SUNLIGHT"]
filtered = sp.signal.savgol_filter(sunlight, window_length=10, polyorder=2)

sunlight_cache = []
look_back = 10

look_ahead = 50

predictions = {}
predictions = {i: [] for i in range(look_ahead)}
predictions["coeff_1"] = [] # leading term
predictions["coeff_2"] = []
predictions["coeff_3"] = []
index = []

for idx, row in df.iterrows():
    sunlight = row["SUNLIGHT"]
    sunlight_cache.append(sunlight)
    sunlight_cache = sunlight_cache[-look_back:]
     
    n = len(sunlight_cache)
    if n < 10:
        continue

    coeffs = np.polyfit(np.arange(n), np.array(sunlight_cache), deg = 2)
    p = np.poly1d(coeffs)

    [predictions[i].append(p(n-1 + i)) for i in range(look_ahead)]
    predictions["coeff_1"].append(coeffs[0])
    predictions["coeff_2"].append(coeffs[1])
    predictions["coeff_3"].append(coeffs[2])
    
    index.append(idx)

predictions = pd.DataFrame(data=predictions, index=index)
predictions["TRUTH"] = df["SUNLIGHT"]

for i in range(look_ahead):
    x = predictions[i].values
    y = predictions["TRUTH"].shift(i+1).values

    x = np.ma.masked_invalid(x)
    y = np.ma.masked_invalid(y)

    print(i, np.ma.corrcoef(x, y)[0, 1])

plt.plot(df["SUNLIGHT"])
plt.plot(predictions[10])
plt.show()



