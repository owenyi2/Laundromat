import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("prices.csv", header=None, skiprows=1, nrows=10000)

fair = df[df[0]=="fair"][1].values
midprice = df[df[0]=="midprice"][1].values

plt.plot(midprice, label="midprice")
plt.plot(fair, label="fairprice")
plt.legend(loc="best")
plt.show()


