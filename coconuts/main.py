import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

day = 3
file_name = f"round-4-island-data-bottle/prices_round_4_day_{day}.csv"

df = pd.read_csv(file_name, sep=";")

coconut_df = df[df["product"] == "COCONUT"].reset_index(drop=True)
coupon_df = df[df["product"] == "COCONUT_COUPON"].reset_index(drop=True)

returns = coconut_df["mid_price"] / coconut_df["mid_price"].shift(1) - 1
mu = returns.mean()
sigma = returns.std()

x = np.linspace(-0.001, 0.001, 100)

# plt.plot(x, norm.pdf(x, mu, sigma))
# plt.hist(returns, bins=20, density=True)
# plt.show()

K = 10000 # Strike Price
T = 250 * 100 # Expiration
r = 0.00

def coupon(t, S_t): # t' is in number of timesteps (100 / round) not timestamps (1M per round)
    d_plus = 1 / (sigma * np.sqrt(T-t)) * (np.log(S_t / K) + (r + sigma**2 / 2) * (T - t))
    d_minus = d_plus - sigma * np.sqrt(T-t)

    price = norm.cdf(-d_minus)*K*np.exp(-r * (T-t)) - norm.cdf(-d_plus) * S_t

    return price

t = np.linspace(0, T-2, 1000)
S_t = np.linspace(K-2000, K+2000, 1000)
T, S = np.meshgrid(t, S_t)

coupon(T, S)
