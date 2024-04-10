import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, Optional
import collections
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
    def compute_amethysts_order(self, state: TradingState):  
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
    
    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            self.traderData = {}
        else:
            self.traderData = json.loads(state.traderData)        

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        orders = {}
        conversions = 0

        self.parse_trader_data(state)
        orders["AMETHYSTS"] = self.compute_amethysts_order(state)
         
        traderData = json.dumps(self.traderData)
        logger.flush(state, orders, conversions, traderData)
        return orders, conversions, traderData
