import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
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

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[:max_length - 3] + "..."

logger = Logger()

class Trader:
    POSITION_LIMIT = 20
    AMETHYSTS_FAIR_VALUE = 10000

    def handle_amethysts(self, state: TradingState) -> tuple[list[Order]]:
        amethysts_orders = []
        curr_pos_constant = state.position.get("AMETHYSTS", 0)
        curr_pos = state.position.get("AMETHYSTS", 0)

        # Market Take
        sell_orders = state.order_depths["AMETHYSTS"].sell_orders
        buy_orders = state.order_depths["AMETHYSTS"].buy_orders
        
        # We buy here
        for ask, vol in sell_orders.items():
            # If the ask price is less than the fair value of AMETHYSTS, or the current position is negative (we have shorted the stock) and the ask price is equal to the fair value, and the current position is less than the limit
            if ((ask < self.AMETHYSTS_FAIR_VALUE) or ((curr_pos_constant < 0) and (ask == self.AMETHYSTS_FAIR_VALUE))) and curr_pos < self.POSITION_LIMIT['AMETHYSTS']:
                order_for = min(-vol, self.POSITION_LIMIT['AMETHYSTS'] - curr_pos)
                curr_pos += order_for
                assert(order_for >= 0)
                amethysts_orders.append(Order("AMETHYSTS", ask, order_for))

        # We sell here
        for bid, vol in buy_orders.items():
            if ((bid > self.AMETHYSTS_FAIR_VALUE) or ((curr_pos_constant > 0) and (bid == self.AMETHYSTS_FAIR_VALUE))) and curr_pos > -self.POSITION_LIMIT['AMETHYSTS']:
                order_for = max(-vol, -self.POSITION_LIMIT['AMEcTHYSTS'] - curr_pos)
                # order_for is a negative number denoting how much we will sell
                curr_pos += order_for
                assert(order_for <= 0)
                amethysts_orders.append(Order("AMETHYSTS", bid, order_for))
        
        # # Market Make
        # best_buy = filter(lambda x: x[0] < self.AMETHYSTS_FAIR_VALUE, buy_orders.items())
        # best_sell = filter(lambda x: x[0] > self.AMETHYSTS_FAIR_VALUE, sell_orders.items())

        # if (curr_pos < self.POSITION_LIMIT['AMETHYSTS']) and (self.position[product] < 0):
        #     num = min(40, self.POSITION_LIMIT['PEARLS'] - cpos)
        #     orders.append(Order(product, min(undercut_buy + 1, acc_bid-1), num))
        #     cpos += num


    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        result = {}
        conversions = 0
        trader_data = ""

        # TODO: Add logic
        result["AMETHYSTS"] = self.handle_amethysts()

        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data
    