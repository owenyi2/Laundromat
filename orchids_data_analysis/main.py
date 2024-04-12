import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

file_name = "round-2-island-data-bottle/prices_round_2_day_-1.csv"

df = pd.read_csv(file_name, sep=";")

print(df)

fig, ax = plt.subplots(2, 1, figsize=(10, 6))
fig.subplots_adjust(right=0.75)

twin01 = ax[0].twinx()
twin02 = ax[0].twinx()
twin03 = ax[0].twinx()

p1, = ax[0].plot(df["ORCHIDS"], label="ORCHIDS", color="tab:blue")
p2, = twin01.plot(df["TRANSPORT_FEES"], label="TEMPERATURE", color="tab:orange")
p3, = twin02.plot(df["EXPORT_TARIFF"], label="EXPORT_TARIFF", color="tab:red")
p4, = twin03.plot(df["IMPORT_TARIFF"], label="IMPORT_TARIFF", color="tab:green")

ax[0].legend(handles=[p1, p2, p3, p4])

twin11 = ax[1].twinx()
twin12 = ax[1].twinx()

p5, = ax[1].plot(df["ORCHIDS"], label="ORCHIDS", color = "tab:blue")
p6, = twin11.plot(df["SUNLIGHT"], label="SUNLIGHT", color= "tab:orange")
p7, = twin12.plot(df["HUMIDITY"], label="HUMIDITY", color= "tab:red")

ax[1].legend(handles=[p5, p6, p7])

plt.show()

