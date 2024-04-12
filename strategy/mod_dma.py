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

    def compute_starfruit_fair_value(self, midprice: int) -> int:
        cache_max = 50

        if len(self.traderData["STARFRUIT"]["MA_cache"]) == cache_max:
            self.traderData["STARFRUIT"]["MA_cache"].pop(0)
        self.traderData["STARFRUIT"]["MA_cache"].append(midprice)
        
        return int(round(self.compute_starfruit_dma(self.traderData["STARFRUIT"]["MA_cache"])))


    def compute_starfruit_sma(self, prices: list, period: int) -> list:
        if not prices or period <= 0:
            return prices
        return [sum(prices[max(0, i-period):i+1]) / min(i+1, period) for i in range(len(prices))]

    def compute_starfruit_ema(self, prices: list, period: int, smoothing: int=2) -> list:
        if not prices or period <= 0:
            return prices
        alpha = smoothing / (period + 1)
        if not isinstance(prices, list):
            return [(prices * alpha) + ((prices * (1 - alpha)))]
        if period > len(prices):
            return prices

        avgs = [self.compute_starfruit_sma(prices, period)[-1]]
        for i in range(1, len(prices)):
            avgs.append((prices[i] * alpha) + (prices[i-1] * (1 - alpha)))

        return avgs

    # DMA Implementation

    def compute_starfruit_wma(self, prices: list, period: int) -> list:
        if not prices or period <= 0:
            return prices
        if not isinstance(prices, list):
            return [prices]
        if period > len(prices):
            return prices

        avgs = []
        weights = [i + 1 for i in range(period)][::-1]
        for i in range(len(prices)):
            if i < period:
                avgs.append(sum(prices[:i+1]) / (i+1))
                continue
            weighted_sum = sum([prices[i - j] * weights[j] for j in range(period)])
            avgs.append(weighted_sum / sum(weights))

        return avgs

    def compute_starfruit_hma(self, prices: list, period: int) -> int:
        if not prices or period <= 0 or period > len(prices):
            return prices
        return self.compute_starfruit_wma(2 * self.compute_starfruit_wma(prices, int(period / 2))[-1] - self.compute_starfruit_wma(prices, period)[-1], int(np.sqrt(period)))

    def compute_starfruit_ehma(self, prices: list, period: int) -> list:
        if not prices or period <= 0 or period > len(prices):
            return prices
        return self.compute_starfruit_ema(2 * self.compute_starfruit_ema(prices, int(period / 2))[-1] - self.compute_starfruit_ema(prices, period)[-1], int(np.sqrt(period)))

    # Translated from: https://www.tradingview.com/script/8MEEEGWl-Dickinson-Moving-Average-DMA/
    def compute_starfruit_dma(self, prices: list, wma_mode=True) -> list:
        # inputs
        hull_length = 8
        ema_length = 28
        ema_gain_limit = 42
        least_error = 1000000.0

        price = prices[-1]

        #dma
        alpha = 2 / (ema_length + 1)
        ema_initial = self.compute_starfruit_ema(prices, ema_length)[-1]

        gain = 0.0
        best_gain = 0.0
        error = 0.0
        ema_current = 0.0

        avgs = []
        for i in range(ema_gain_limit):
            gain = i / 10
            ema_current = alpha * (ema_initial + gain * (price - ema_current)) + (1 - alpha) * ema_current # CHECK
            error = abs(price - ema_current) # CHECK
            if error < least_error:
                least_error = error
                best_gain = gain

        ema_current = alpha * (ema_initial + best_gain * (price - ema_current)) + (1 - alpha) * ema_current # CHECK

        if wma_mode:
            return (ema_current + self.compute_starfruit_hma(prices, hull_length)[-1]) / 2
        return (ema_current + self.compute_starfruit_ehma(prices, hull_length)[-1]) / 2

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
        fair_value = self.compute_starfruit_fair_value(midprice)

        # compare with crossover using 50 day sma then 20 day sma
        fiftydma = self.compute_starfruit_sma(self.traderData["STARFRUIT"]["MA_cache"], 50)
        twentydma = self.compute_starfruit_sma(self.traderData["STARFRUIT"]["MA_cache"], 20)
        golden_cross = False
        if len(fiftydma) > 1 and fiftydma[-1] > fair_value and fiftydma[-2] <= fair_value:
            if twentydma[-1] > fair_value and twentydma[-2] <= fair_value:
                golden_cross = True
        death_cross = False
        if len(fiftydma) > 1 and fiftydma[-1] < fair_value and fiftydma[-2] >= fair_value:
            if twentydma[-1] < fair_value and twentydma[-2] >= fair_value:
                death_cross = True

        print(f"{fair_value},{midprice}")
        #print(f"fair,{fair_value}")
        #print(f"midprice,{midprice}")

        # borrowed from owyi branch
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

        # SUBMIT BUY ORDERS
        cpos = position

        for ask, vol in osell.items():
            if cpos < POSITION_LIMIT and ((golden_cross and ask <= fair_value) or ask <= min(previous_ask - 4, fair_value)):
                order_for = min(-vol, POSITION_LIMIT - cpos)
                cpos += order_for
                orders.append(Order("STARFRUIT", ask, order_for))

        """if cpos < POSITION_LIMIT:
            num = POSITION_LIMIT - cpos
            orders.append(Order("STARFRUIT", bid_pr, num))
            cpos += num"""

        # SUBMIT SELL ORDERS
        cpos = position

        for bid, vol in obuy.items():
            if cpos > -POSITION_LIMIT and ((death_cross and bid >= fair_value) or bid >= max(previous_bid + 4, fair_value)):
                order_for = max(-vol, -POSITION_LIMIT-cpos)
                cpos += order_for
                orders.append(Order("STARFRUIT", bid, order_for))

        """if cpos > -POSITION_LIMIT:
            num = -POSITION_LIMIT-cpos
            orders.append(Order("STARFRUIT", sell_pr, num))
            cpos += num"""

        return orders

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            # Init KF filter for STARFRUIT
            order_depth = state.order_depths["STARFRUIT"]
            mid_price = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys())) / 2.0
            P = np.eye(3) * 0.01 # State Uncertainty (diag)
            x = np.array([[mid_price],[0], [0]]) # Initial state
            #self.traderData = {"STARFRUIT": {"previous_ask": 1e9, "previous_bid": -1e9, "KF_state": jsonpickle.encode((x, P))}}
            self.traderData = {"STARFRUIT": {"previous_ask": 1e9, "previous_bid": -1e9, "MA_cache": []}}
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
