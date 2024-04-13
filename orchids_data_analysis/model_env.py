import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

pd.options.mode.chained_assignment = None
file_name = "round-2-island-data-bottle/prices_round_2_day_-1.csv"
PREDICTIONS = 20

DF_raw = pd.read_csv(file_name, sep=";")
DF = DF_raw[["timestamp", "SUNLIGHT", "HUMIDITY"]]
#print(DF)
model = LinearRegression()

def predict(df, key, model, learn=10):
    prev = df.tail(learn)
    prev["timestamp_sq"] = prev["timestamp"] ** 2

    X = prev[["timestamp", "timestamp_sq"]].to_numpy()

    time = prev["timestamp"].to_numpy()
    next_time = time[-1] + 1
    y = prev[key].to_numpy()

    model.fit(X, y)

    pred_feat = np.array([next_time, next_time ** 2])
    pred_val = model.predict([pred_feat])[0]

    return next_time, pred_val

print("timestamp,SUNLIGHT,HUMIDITY")
for i in range(PREDICTIONS):
    t, sun = predict(DF, "SUNLIGHT", model)
    t, hum = predict(DF, "HUMIDITY", model)
    DF.loc[len(DF.index)] = [t, sun, hum]
    print(f"{t},{sun},{hum}")

plot_sun = plt.subplot2grid((3, 4), (0, 0), rowspan=2, colspan=2)
plot_sun.plot(DF["timestamp"], DF["SUNLIGHT"], 'orange')
plot_sun.set_title("Sunlight Predictions")

plot_hum = plt.subplot2grid((3, 4), (0, 2), rowspan=2, colspan=2)
plot_hum.plot(DF["timestamp"], DF["HUMIDITY"], 'tab:blue')
plot_hum.set_title("Humidity Predictions")

plot_uni = plt.subplot2grid((3, 4), (2, 0), rowspan=2, colspan=4)
plot_uni.plot(DF["timestamp"], DF["SUNLIGHT"], 'orange', label="Sunlight")
plot_uni.plot(DF["timestamp"], DF["HUMIDITY"], 'tab:blue', label="Humidity")
plot_uni.set_title("Unified Predictions")

plt.tight_layout()
plt.legend()
plt.show()
