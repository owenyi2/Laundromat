import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, Optional
import collections
import jsonpickle
from copy import deepcopy
import numpy as np

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

class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        print(json.dumps([
            self.compress_state(state),
            self.compress_orders(orders),
            conversions,
            trader_data,
            self.logs,
        ], cls=ProsperityEncoder, separators=(",", ":")))

        self.logs = ""

    def compress_state(self, state: TradingState) -> list[Any]:
        return [
            state.timestamp,
            state.traderData,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

logger = Logger()

class Trader:
    def orchids_apply_kalman(self, kf_state, midprice):
        x, P = jsonpickle.decode(kf_state)

        F = np.array([[1,1,.5],    # State Transition Model
                      [0,1,1],
                      [0,0,1]])  
        H = np.array([[1, 0, 0]]) # Observation matrix
        R = np.eye(1)             # Measurement Noise (diag)
        Q = np.eye(3) * 1e-9# Process Noise     (diag) 

        x, P = KF_predict(x, P, F, Q)
        x, P = KF_update(midprice, x, P, H, R) 

        self.traderData["ORCHIDS"]["KF_state"] = jsonpickle.encode((x, P))

        return x[1, 0]

    def handle_orchids(self, state: TradingState) -> tuple[list[Order], int]:
        position = state.position.get("ORCHIDS", 0)
        order_depth: OrderDepth = state.order_depths["ORCHIDS"]
        orders: list[Order] = []

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        POSITION_LIMIT = 100
        DESIRED_NEUTRAL_POSITION = -50
        best_ask_pr = min(osell.keys())
        best_bid_pr = max(obuy.keys())

        midprice = (best_ask_pr + best_bid_pr) / 2.0

        # So the bid ask spread is quite shit.
        # If we trade by taking the domestic bid and taking the international ask, the spread is more favourable

        price_velocity = self.orchids_apply_kalman(self.traderData["ORCHIDS"]["KF_state"], midprice)
        logger.print(price_velocity)
        
        desired_position = max(-POSITION_LIMIT, int(round(POSITION_LIMIT * price_velocity)) + DESIRED_NEUTRAL_POSITION)
        conversion = 0
        max_deviation = 5

        # We need a method to determine when domestic prices are high so we can short them
        # And then a method to know when international prices are low so we can close our shorts all at once.

        if position < desired_position and abs(position - desired_position) > max_deviation: # we want to buy
            # REPLACE WITH CONVERSION
            ask, vol = next(iter(osell.items()))
            buy_volume = min(desired_position - position, -vol) 
            order_for = min(buy_volume, POSITION_LIMIT - position)
            conversion = max(-position, order_for)
        
        if position > desired_position and abs(position - desired_position) > max_deviation: # we want to sell
            bid, vol = next(iter(obuy.items()))
            sell_volume = max(desired_position - position, -vol)
            order_for = max(sell_volume, -POSITION_LIMIT - position)
            orders.append(Order("ORCHIDS", bid, order_for))
            
        return orders, conversion

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            # Init KF filter for ORCHIDS
            order_depth = state.order_depths["ORCHIDS"] 
            mid_price = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys())) / 2.0
            P = np.eye(3) * 0.01 # State Uncertainty (diag) 
            x = np.array([[mid_price],[0], [0]]) # Initial state
            self.traderData = {"ORCHIDS": {"KF_state": jsonpickle.encode((x, P))}} 
        else:
            self.traderData = json.loads(state.traderData) 

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        orders = {}
        conversions = 0

        self.parse_trader_data(state)
        orders["ORCHIDS"], conversions = self.handle_orchids(state) 

        traderData = json.dumps(self.traderData)
        logger.flush(state, orders, conversions, traderData)
        return orders, conversions, traderData
