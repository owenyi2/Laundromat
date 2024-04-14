from copy import deepcopy
import numpy as np
import jsonpickle
import pandas as pd
import matplotlib.pyplot as plt

def reshape_z(z, dim_z, ndim):
    """ensure z is a (dim_z, 1) shaped vector"""

    z = np.atleast_2d(z)
    if z.shape[1] == dim_z:
        z = z.T

    if z.shape != (dim_z, 1):
        raise ValueError(
            "z (shape {}) must be convertible to shape ({}, 1)".format(z.shape, dim_z)
        )

    if ndim == 1:
        z = z[:, 0]

    if ndim == 0:
        z = z[0, 0]

    return z

# X :: State Matrix
# P :: State Uncertainty
# Q :: Process Uncertainty
# R :: Measurement Uncertainty
# F :: State Transition
# H :: Observation Matrix

# code sourced from <https://github.com/rlabbe/filterpy/blob/master/filterpy/kalman/kalman_filter.py#L133C7-L133C19> and <https://arxiv.org/ftp/arxiv/papers/1204/1204.0375.pdf> with modifications

def KF_predict(X, P, F, Q):
    X = np.dot(F, X)
    P = np.dot(F, np.dot(P, F.T)) + Q

    return X, P

def KF_update(z, X, P, H, R):
    Z = reshape_z(z, 1, 3) 

    PHT = np.dot(P, H.T)
    S = np.dot(H, PHT) + R
    SI = np.linalg.inv(S) 

    K = np.dot(PHT, SI)

    IM = np.dot(H, X)
    X = X + np.dot(K, (Z-IM))

    _I = np.eye(3)
    I_KH = _I - np.dot(K, H)
    P = np.dot(np.dot(I_KH, P), I_KH.T) + np.dot(np.dot(K, R), K.T)

    return X, P

df = pd.read_csv("parse/merged_data.csv", index_col = 0)
print(df)
orchid_prices = df["mid_price"].values

P = np.eye(3) * 1e-5 # State Uncertainty (diag) 
x = np.array([[orchid_prices[0]],[0], [0]]) # Initial state
traderData = {"STARFRUIT": {"previous_ask": 1e9, "previous_bid": -1e9, "KF_state": jsonpickle.encode((x, P))}}

F = np.array([[1,1, .5],    # State Transition Model
                 [0,1, 1],
                 [0, 0, 1]])

H = np.array([[1, 0, 0]])
R = np.eye(1)         # Measurement Noise (diag)
Q = np.eye(3) * 1e-9 # Process Noise     (diag)

X = []
M = []
X_dot = []

num_iter = 1000 
T = np.arange(num_iter)

for t in T:
    x, P = KF_predict(x, P, F, Q)
   
    price = orchid_prices[t]
    M.append(price)

    x, P = KF_update(price, x, P, H, R)

    X.append(x[0, 0])
    X_dot.append(x[1, 0])

M = pd.Series(data=M, index=T)
X = pd.Series(data=X, index=T)

fig, ax = plt.subplots(1, 1, figsize=(10, 6))

ax.plot(M.astype(int))
ax.plot(X.astype(int))

twin1 = ax.twinx()
twin1.plot(X_dot, color="tab:green")
twin1.plot(pd.Series(data=0, index=T))

plt.show()
