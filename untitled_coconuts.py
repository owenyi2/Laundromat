import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, Optional
import collections
import jsonpickle
from copy import deepcopy
import numpy as np


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
    def handle_baskets(self, state: TradingState):
        positions = {}
        osell = {}
        obuy = {}
        midprice = {}

        composition = {"COCONUT": 1, "COCONUT_COUPON": -2}

        POSITION_LIMIT = 300  
        for product in composition.keys():
            positions[product] = state.position.get(product, 0)
            order_depth = state.order_depths[product]
            osell[product] = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
            obuy[product] = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))
            
            if len(osell[product]) == 0 or len(obuy[product]) == 0:
                return [], []

            best_ask_pr = min(osell[product].keys())
            best_bid_pr = max(obuy[product].keys())
        
            midprice[product] = (best_ask_pr + best_bid_pr) / 2
        
        synthetic_price = midprice["COCONUT"] - 2 * midprice["COCONUT_COUPON"] 
        z_score = (synthetic_price - 8730) / 26.77 
        smooth_span = 100.0
        alpha = 2.0 /(smooth_span+1)

        previous_ema = self.traderData["COCONUT"]["z_score_ema"] 
        if previous_ema is None:
            z_score_smooth = z_score
        else:
            self.traderData["COCONUT"]
            z_score_smooth = alpha * z_score + (1-alpha) * previous_ema
        
        self.traderData["COCONUT"]["z_score_ema"] = z_score_smooth

        forecast = -np.clip(z_score_smooth, -1, 1)

        desired_position = forecast * POSITION_LIMIT
        current_position = positions["COCONUT"]

        logger.print("desired_position", desired_position)
        logger.print("current_position", current_position)
        logger.print("z_score", z_score)
        logger.print("synthetic_price", synthetic_price)

        threshold = 0.05

        if desired_position > current_position and abs(current_position / desired_position - 1) > threshold:
            # buy COCONUT sell COCONUT_COUPONS 
            logger.print("BUY")
            order_vol = 1e9
            product_price = {}

            product_price["COCONUT"], vol = next(iter(osell["COCONUT"].items()))
            order_vol = min(order_vol, int(vol / -composition["COCONUT"]))

            product_price["COCONUT_COUPON"], vol = next(iter(obuy["COCONUT_COUPON"].items()))
            order_vol = min(order_vol, int(vol / -composition["COCONUT_COUPON"]))

            order_vol = min(order_vol, int(desired_position - current_position))
           
            orders = []
            for product in composition.keys(): 
                orders.append([Order(product, product_price[product], order_vol * composition[product])]) 
            # return tuple(orders)
            # return orders[0], orders[1] 
            return [], orders[1]

        elif desired_position < current_position and abs(current_position / desired_position - 1) > threshold:
            # sell coconut buy coupon

            logger.print("SELL")
            order_vol = 1e9
            product_price = {}

            product_price["COCONUT"], vol = next(iter(obuy["COCONUT"].items()))
            order_vol = min(order_vol, int(vol / -composition["COCONUT"]))

            product_price["COCONUT_COUPON"], vol = next(iter(osell["COCONUT_COUPON"].items()))
            order_vol = min(order_vol, int(vol / -composition["COCONUT_COUPON"]))

            order_vol = min(order_vol, int(current_position - desired_position))
           
            orders = []
            for product in composition.keys(): 
                orders.append([Order(product, product_price[product], order_vol * composition[product])])
            # return tuple(orders)
            # return orders[0], orders[1] 
            return [], orders[1]
        else:
            return [], []

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            self.traderData = {"COCONUT": {"z_score_ema": None}} 
        else:
            self.traderData = json.loads(state.traderData) 

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        orders = {}
        conversions = 0

        self.parse_trader_data(state)
        orders["COCONUT"], orders["COCONUT_COUPON"] = self.handle_baskets(state) 

        traderData = json.dumps(self.traderData)
        logger.flush(state, orders, conversions, traderData)
        return orders, conversions, traderData
