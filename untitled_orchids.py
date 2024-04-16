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
    def handle_orchids(self, state: TradingState) -> tuple[list[Order], int]:
        position = state.position.get("ORCHIDS", 0)
        order_depth: OrderDepth = state.order_depths["ORCHIDS"]
        orders: list[Order] = []
        conversion: int = 0

        alpha = 2.0 / (50 + 1)

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        observation: Observation = state.observations.conversionObservations["ORCHIDS"]

        POSITION_LIMIT = 100

        DOMESTIC_LOOKBACK = 10
        INTERNATIONAL_LOOKBACK = 50
        
        domestic_bid = max(obuy.keys())

        international_ask = observation.askPrice
        transport_fee = observation.transportFees
        import_tariff = observation.importTariff 

        real_international_ask = international_ask + transport_fee + import_tariff

        domestic_ema = self.traderData["ORCHIDS"]["domestic_ema"]
        if domestic_ema: 
            domestic_ema = alpha * domestic_bid + (1-alpha) * domestic_ema
        else:
            domestic_ema = domestic_bid
        self.traderData["ORCHIDS"]["domestic_ema"] = domestic_ema

        real_international_ema = self.traderData["ORCHIDS"]["real_international_ema"]
        if real_international_ema: 
            real_international_ema = alpha * real_international_ask + (1-alpha) * real_international_ema
        else:
            real_international_ema = real_international_ask
        self.traderData["ORCHIDS"]["real_international_ema"] = real_international_ema

        domestic_bid_hist = self.traderData["ORCHIDS"]["domestic_bid"]
        domestic_bid_hist.append(domestic_bid - domestic_ema)
        domestic_bid_hist = domestic_bid_hist[-DOMESTIC_LOOKBACK:]
        self.traderData["ORCHIDS"]["domestic_bid"] = domestic_bid_hist

        real_international_ask_hist = self.traderData["ORCHIDS"]["real_international_ask"]
        real_international_ask_hist.append(real_international_ask - real_international_ema)
        real_international_ask_hist = real_international_ask_hist[-INTERNATIONAL_LOOKBACK:]
        self.traderData["ORCHIDS"]["real_international_ask"] = real_international_ask_hist


        cpos = position

        if len(domestic_bid_hist) == DOMESTIC_LOOKBACK:
            domestic_bid_hist = np.array(domestic_bid_hist)
            z_score = (domestic_bid_hist[-1] - domestic_bid_hist.mean())/domestic_bid_hist.std()

            logger.print("domestic_bid z_score", z_score)

            if z_score > .5:
                bid, vol = next(iter(obuy.items()))
                order_for = max(-vol, -POSITION_LIMIT - cpos)
                cpos += order_for 
                orders.append(Order("ORCHIDS", bid, order_for))

        if len(real_international_ask_hist) == INTERNATIONAL_LOOKBACK:
            real_international_ask_hist = np.array(real_international_ask_hist)
            z_score = (real_international_ask_hist[-1] - real_international_ask_hist.mean()) / real_international_ask_hist.std()

            logger.print("real_international_ask z_score", z_score)

            if z_score < -.5 and cpos < 0:
                conversion = -cpos

        return orders, conversion

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            self.traderData = {"ORCHIDS": {"domestic_bid": [], "real_international_ask": [], "domestic_ema": None, "real_international_ema": None}} 
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
