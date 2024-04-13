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
    def compute_orchids_fair_value(self, best_bid, best_ask):
        bid_gain = .5
        ask_gain = .5 
        threshold = 1

        if self.traderData["ORCHIDS"]["adjusted_bid"] is None:
            adjusted_bid = best_bid
        else:
            previous_adjusted_bid = self.traderData["ORCHIDS"]["adjusted_bid"]
            previous_bid = self.traderData["ORCHIDS"]["previous_bid"]
            adjusted_bid = (previous_adjusted_bid + previous_bid * bid_gain) / (1 + bid_gain)
        
        if best_bid >= adjusted_bid + threshold:
            self.traderData["ORCHIDS"]["adjusted_bid"] = adjusted_bid
        else:
            self.traderData["ORCHIDS"]["adjusted_bid"] = best_bid
        self.traderData["ORCHIDS"]["previous_bid"] = best_bid

        if self.traderData["ORCHIDS"]["adjusted_ask"] is None:
            adjusted_ask = best_ask
        else:
            previous_adjusted_ask = self.traderData["ORCHIDS"]["adjusted_ask"]
            previous_ask = self.traderData["ORCHIDS"]["previous_ask"]
            adjusted_ask = (previous_adjusted_ask + previous_ask * ask_gain) / (1 + ask_gain)

        if best_ask <= adjusted_ask - threshold:
            self.traderData["ORCHIDS"]["adjusted_ask"] = adjusted_ask
        else:
            self.traderData["ORCHIDS"]["adjusted_ask"] = best_ask
        self.traderData["ORCHIDS"]["previous_ask"] = best_ask
        
        fair_price = (self.traderData["ORCHIDS"]["adjusted_ask"] + self.traderData["ORCHIDS"]["adjusted_bid"]) / 2.0 
       
        return int(round(fair_price))

    def handle_orchids(self, state: TradingState) -> tuple[list[Order], int]:
        position = state.position.get("ORCHIDS", 0)
        order_depth: OrderDepth = state.order_depths["ORCHIDS"]
        observation: Observation = state.observations.conversionObservations["ORCHIDS"]

        logger.print(jsonpickle.encode(observation)) # important for the regex parsing of output

        orders: list[Order] = []
        conversions: int = 0
         
        POSITION_LIMIT = 100

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        best_ask_pr = min(osell.keys())
        best_bid_pr = max(obuy.keys())
 
        fair_value = self.compute_orchids_fair_value(best_bid_pr, best_ask_pr)
     
        if position > 10: # 10 < position <= 20
            bid_adjust = -3
            ask_adjust = +1
        elif position >= 5: # 5 <= position <= 10
            bid_adjust = -3
            ask_adjust = +2
        elif position > -5: # -5 < position < 5
            bid_adjust = -2
            ask_adjust = +2
        elif position >= -10: # -10 <= position <= 5
            bid_adjust = -2
            ask_adjust = +3
        else: # -20 <= position < -10
            bid_adjust = -1
            ask_adjust = +3

        our_bid = fair_value + bid_adjust
        our_ask = fair_value + ask_adjust

        bid_pr = min(best_bid_pr + 1, our_bid) # we will shift this by 1 to beat this price
        sell_pr = max(best_ask_pr - 1, our_ask)

        cpos = position

        if cpos < POSITION_LIMIT:
            num = POSITION_LIMIT - cpos
            orders.append(Order("ORCHIDS", bid_pr, num))
            cpos += num

        cpos = position

        if cpos > -POSITION_LIMIT:
            num = -POSITION_LIMIT-cpos
            orders.append(Order("ORCHIDS", sell_pr, num))
            cpos += num
        
        return orders, conversions 

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            self.traderData = {"ORCHIDS": {"previous_ask": None, "adjusted_ask": None, "adjusted_bid": None, "previous_bid": None}}
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
