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
        observation: Observation = state.observations.conversionObservations["ORCHIDS"]

        logger.print(observation)
        logger.print(jsonpickle.encode(observation))

        orders: list[Order] = []
        conversions: int = 0
         
        POSITION_LIMIT = 100



        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        import_askprice = observation.askPrice
        transport_fee = observation.transportFees
        import_tariff = observation.importTariff # generally negative i.e. obtain for importing
        uncertainty = 2

        procurement_cost = import_askprice + transport_fee + import_tariff + uncertainty

        logger.print(procurement_cost)

        cpos = position

        for bid, vol in obuy.items():
            if (bid >= procurement_cost) and cpos > -POSITION_LIMIT: 
                order_for = max(-vol, -POSITION_LIMIT-cpos)
                cpos += order_for
                orders.append(Order("STARFRUIT", bid, order_for))
                conversions -= order_for

        logger.print(conversions)

        # IMPLEMENT AN IMPORTER STRATEGY

        # Estimate the lowest price you can feasibly import for
          # This will be current ASK + import premia (negative) + transport cost + UNCERTAINTY
          # UNCERTAINTY is due to the fact that ASK may increase on the next timestamp
        # Market Take any bids whose bid price is above this 
        # Accumulate an overall negative position so as to avoid Storage costs
        
        return orders, conversions 

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            self.traderData = {"STARFRUIT": {"previous_ask": None, "adjusted_ask": None, "adjusted_bid": None, "previous_bid": None}}
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
