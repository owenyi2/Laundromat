import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

df = pd.read_csv("activity.csv", sep=";")
df = df[df["product"] == "STARFRUIT"]

mid_price = df["mid_price"]

data_df = pd.DataFrame(index=df.index.copy())

data_df["X"] = mid_price
data_df["Ms"] = mid_price.ewm(alpha=0.01).mean()
data_df["Mf"] = mid_price.ewm(alpha=0.1).mean()
data_df["y"] = mid_price.shift(-1)

data_df = data_df.dropna()

X = data_df.iloc[:, :3].to_numpy()
y = data_df.iloc[:, -1].to_numpy()

TEST_TRAIN_SPLIT = 1500 # how many test samples

reg = LinearRegression(fit_intercept=False).fit(X[:-TEST_TRAIN_SPLIT], y[:-TEST_TRAIN_SPLIT])

print(reg.coef_)
print(reg.intercept_)

# Performance on Training set
prediction = reg.predict(X[:-TEST_TRAIN_SPLIT]).astype(int)
target = y[:-TEST_TRAIN_SPLIT].astype(int)
print("Training MSE: ", np.square(prediction - target).mean())

fig, ax = plt.subplots(2, 1, figsize=(3, 9))

# Performance on Test set
prediction = reg.predict(X[-TEST_TRAIN_SPLIT:]).astype(int)
target = y[-TEST_TRAIN_SPLIT:].astype(int)
ax[0].scatter(prediction, target) # Regression on slow and fast EMA
print("Testing MSE: ", np.square(prediction - target).mean())

# Previous Value as Baseline
prediction = X[-TEST_TRAIN_SPLIT:, 0].astype(int)
target = y[-TEST_TRAIN_SPLIT:].astype(int)
ax[1].scatter(prediction, target) # previous value
print("Baseline predictor MSE: ", np.square(prediction - target).mean())

plt.show()
