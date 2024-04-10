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

# SMA Implementations

def SMA_standard(self, prices: list, period: int) -> list:
    if not prices or period <= 0 or period > len(prices):
        return -1

    avgs = []
    for i in range(len(prices)):
        avgs.append(sum(prices[max(0, i-period):i+1]) / min(i+1, period))

    return avgs

def SMA_responsive(self, prices: list, period: int) -> list:
    if not prices or period <= 0 or period > len(prices):
        return -1

    avgs = []
    for i in range(len(prices)):
        if i < period:  # fill le first period
            avgs.append(sum(prices[:i+1]) / (i+1))
            continue

	delta = (prices[i] - prices[i-period]) / period
        avgs.append(avgs[i-1] + delta)

    return avgs

# EMA Implementations

def EMA_standard(prices: List, period: int) -> list:
    return []

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
    def compute_amethysts_order(self, state: TradingState) -> list[Order]:
        position = state.position.get("AMETHYSTS", 0)
        order_depth: OrderDepth = state.order_depths["AMETHYSTS"]
        fair_value = 10000

        orders: list[Order] = []
        POSITION_LIMIT = 20

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        best_sell_pr = list(filter(lambda x: x > fair_value, osell.keys()))[0]
        best_buy_pr = list(filter(lambda x: x < fair_value, obuy.keys()))[0]

        undercut_buy = best_buy_pr + 1
        undercut_sell = best_sell_pr - 1

        # SUBMIT BUY ORDERS
        cpos = position

        for ask, vol in osell.items():
            if ((ask < fair_value) or ((position < 0) and (ask == fair_value))) and cpos < POSITION_LIMIT:
                order_for = min(-vol, POSITION_LIMIT - cpos)
                cpos += order_for
                orders.append(Order("AMETHYSTS", ask, order_for))

        if cpos < POSITION_LIMIT:
            num = min(40, POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", min(undercut_buy, fair_value-1), num))
            cpos += num

        # SUBMIT SELL ORDERS
        cpos = position

        for bid, vol in obuy.items():
            if ((bid > fair_value) or ((position > 0) and (bid == fair_value))) and cpos > -POSITION_LIMIT:
                order_for = max(-vol, -POSITION_LIMIT - cpos)
                cpos += order_for
                orders.append(Order("AMETHYSTS", bid, order_for))

        if cpos > -POSITION_LIMIT:
            num = max(-40, -POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", max(undercut_sell, fair_value+1), num))
            cpos += num

        return orders

    def compute_starfruit_fair_value(self, kf_state, midprice_measurement):
        x, P = jsonpickle.decode(kf_state)
        # print(x, P)
        #
        # print(midprice_measurement)
        # input()

        F = np.array([[1,1,.5],    # State Transition Model
                      [0,1,1],
                      [0,0,1]])
        H = np.array([[1, 0, 0]]) # Observation matrix
        R = np.eye(1)             # Measurement Noise (diag)
        Q = np.eye(3) * 0.00001                  # Process Noise     (diag)

        x, P = KF_predict(x, P, F, Q)
        x, P = KF_update(midprice_measurement, x, P, H, R)

        self.traderData["STARFRUIT"]["KF_state"] = jsonpickle.encode((x, P))

        return int(round(x[0, 0]))

    def compute_starfruit_order(self, state: TradingState) -> list[Order]:
        position = state.position.get("STARFRUIT", 0)
        order_depth: OrderDepth = state.order_depths["STARFRUIT"]

        orders: list[Order] = []
        POSITION_LIMIT = 20

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        best_ask_pr = min(osell.keys())
        best_bid_pr = max(obuy.keys())

        previous_ask = self.traderData["STARFRUIT"]["previous_ask"]
        self.traderData["STARFRUIT"]["previous_ask"] = best_ask_pr
        previous_bid = self.traderData["STARFRUIT"]["previous_bid"]
        self.traderData["STARFRUIT"]["previous_bid"] = best_bid_pr

        midprice = (best_ask_pr + best_bid_pr) / 2.0
        previous_midprice = (previous_ask + previous_bid) / 2.0
        if previous_midprice == 0:
            midprice_measurement = midprice
        else:
            midprice_measurement = np.clip(midprice, previous_midprice - 2, previous_midprice + 2) # clip outliers
        fair_value = self.compute_starfruit_fair_value(self.traderData["STARFRUIT"]["KF_state"], midprice_measurement)

        print(f"fair,{fair_value}")
        print(f"midprice,{midprice}")

        our_bid = fair_value - 2
        our_ask = fair_value + 2

        bid_pr = min(best_bid_pr + 1, our_bid) # we will shift this by 1 to beat this price
        sell_pr = max(best_ask_pr - 1, our_ask)

        # SUBMIT BUY ORDERS
        cpos = position

        for ask, vol in osell.items():
            if cpos < POSITION_LIMIT and ask <= min(previous_ask - 4, fair_value):
                order_for = min(-vol, POSITION_LIMIT - cpos)
                cpos += order_for
                orders.append(Order("STARFRUIT", ask, order_for))

        if cpos < POSITION_LIMIT:
            num = POSITION_LIMIT - cpos
            orders.append(Order("STARFRUIT", bid_pr, num))
            cpos += num

        # SUBMIT SELL ORDERS
        cpos = position

        for bid, vol in obuy.items():
            if cpos > -POSITION_LIMIT and bid >= max(previous_bid + 4, fair_value):
                order_for = max(-vol, -POSITION_LIMIT-cpos)
                cpos += order_for
                orders.append(Order("STARFRUIT", bid, order_for))

        if cpos > -POSITION_LIMIT:
            num = -POSITION_LIMIT-cpos
            orders.append(Order("STARFRUIT", sell_pr, num))
            cpos += num

        return orders

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            # Init KF filter for STARFRUIT
            order_depth = state.order_depths["STARFRUIT"]
            mid_price = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys())) / 2.0
            P = np.eye(3) * 0.01 # State Uncertainty (diag)
            x = np.array([[mid_price],[0], [0]]) # Initial state
            self.traderData = {"STARFRUIT": {"previous_ask": 1e9, "previous_bid": -1e9, "KF_state": jsonpickle.encode((x, P))}}
        else:
            self.traderData = json.loads(state.traderData)

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        orders = {}
        conversions = 0

        self.parse_trader_data(state)
        orders["AMETHYSTS"] = self.compute_amethysts_order(state)
        orders["STARFRUIT"] = self.compute_starfruit_order(state)

        traderData = json.dumps(self.traderData)
        logger.flush(state, orders, conversions, traderData)
        return orders, conversions, traderData

