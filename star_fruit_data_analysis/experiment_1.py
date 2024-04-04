import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

df = pd.read_csv("activity.csv", sep=";")
df = df[df["product"] == "STARFRUIT"]

mid_price = df["mid_price"]

n = 4
data_df = pd.DataFrame(index=df.index.copy())

for i in range(n):
    data_df[f"X_[{i}]"] = mid_price.shift(i) 

# i.e. X[0] is the latest and X_[k] is the from k-steps ago

data_df["Y"] = mid_price.shift(-1)

data_df = data_df.dropna()

X = data_df.iloc[:, :n].to_numpy()
y = data_df.iloc[:, -1].to_numpy()

TEST_TRAIN_SPLIT = 1000

reg = LinearRegression().fit(X[:-TEST_TRAIN_SPLIT], y[:-TEST_TRAIN_SPLIT])

print(reg.coef_)
print(reg.intercept_)
print(reg.score(X[-TEST_TRAIN_SPLIT:], y[-TEST_TRAIN_SPLIT:]))

plt.plot(y)
plt.plot(reg.predict(X)) # multiple regression 
plt.plot(np.average(X, axis=1, weights = [1/10, 2/10, 3/10, 4/10])) # simple Weighted MovAvg
plt.show()


