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
    def compute_amethysts_order(self, position, order_depth, fair_value): 
        orders: list[Order] = []
        POSITION_LIMIT = 20

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))
        best_sell_pr = list(osell.keys())[0]
        best_buy_pr = list(obuy.keys())[0]

        undercut_buy = best_buy_pr + 1
        undercut_sell = best_sell_pr - 1

        bid_pr = min(undercut_buy, fair_value-1) # we will shift this by 1 to beat this price
        sell_pr = max(undercut_sell, fair_value+1)

        cpos = position

        for ask, vol in osell.items(): 
            if ((ask < fair_value) or ((position < 0) and (ask == fair_value))) and cpos < POSITION_LIMIT:
                order_for = min(-vol, POSITION_LIMIT - cpos)
                cpos += order_for
                orders.append(Order("AMETHYSTS", ask, order_for))        

        if (cpos < POSITION_LIMIT) and (position < 0):
            num = min(40, POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", min(undercut_buy + 1, fair_value-1), num))
            cpos += num

        if (cpos < POSITION_LIMIT) and (position > 15):
            num = min(40, POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", min(undercut_buy - 1, fair_value-1), num))
            cpos += num

        if cpos < POSITION_LIMIT:
            num = min(40, POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", bid_pr, num))
            cpos += num
        
        cpos = position

        for bid, vol in obuy.items():
            if ((bid > fair_value) or ((position > 0) and (bid == fair_value))) and cpos > -POSITION_LIMIT:
                order_for = max(-vol, -POSITION_LIMIT - cpos)
                cpos += order_for
                orders.append(Order("AMETHYSTS", bid, order_for))
        
        if (cpos > -POSITION_LIMIT) and (position > 0):
            num = max(-40, -POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", max(undercut_sell-1, fair_value+1), num))
            cpos += num

        if (cpos > -POSITION_LIMIT) and (position < -15):
            num = max(-40, -POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", max(undercut_sell+1, fair_value+1), num))
            cpos += num

        if cpos > -POSITION_LIMIT:
            num = max(-40, -POSITION_LIMIT - cpos)
            orders.append(Order("AMETHYSTS", sell_pr, num))
            cpos += num

        return orders
    
    def compute_midprice(self, order_depth: OrderDepth) -> Optional[float]:
        if len(order_depth.sell_orders) != 0 or len(order_depth.buy_orders) != 0:
            # At least one is non-empty
            try: 
                best_ask = min(order_depth.sell_orders.keys())
            except ValueError:
                best_bid = max(order_depth.buy_orders.keys())
                return best_bid 
            try:
                best_bid = max(order_depth.buy_orders.keys())
            except ValueError:
                best_ask = min(order_depth.sell_orders.keys())
                return best_ask
            return (best_ask + best_bid) / 2.0
        else:
            return None 

    def compute_ema(self, midprice, previous_ema, alpha): 
        if previous_ema is None:
            ema = midprice
        else:
            ema = alpha * midprice + (1 - alpha) * previous_ema
        return ema

    def compute_starfruit_value(self, midprice, slow_ema, fast_ema) -> int:
        intercept = 0
        coefficients = np.array([0.25641302, -0.03131198, 0.77487554])
 
        predicted_midprice = np.dot(coefficients, [midprice, slow_ema, fast_ema]) + intercept
        predicted_midprice = int(round(predicted_midprice))

        return predicted_midprice

    def compute_starfruit_order(self, position, order_depth, fair_value) -> list[Order]:
        orders: list[Order] = []

        POSITION_LIMIT = 20

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))
        our_bid = fair_value - 2
        our_ask = fair_value + 2

        best_sell_pr = list(osell.keys())[0]
        best_buy_pr = list(obuy.keys())[0]
        undercut_buy = best_sell_pr + 1
        undercut_sell = best_buy_pr - 1 
        bid_pr = min(undercut_buy, our_bid) # we will shift this by 1 to beat this price
        sell_pr = max(undercut_sell, our_ask)

        cpos = position

        for ask, vol in osell.items():
            if ((ask <= our_bid) or ((position<0) and (ask == our_bid+1))) and cpos < POSITION_LIMIT:
                order_for = min(-vol, POSITION_LIMIT - cpos)
                cpos += order_for
                orders.append(Order("STARFRUIT", ask, order_for))

        if cpos < POSITION_LIMIT:
            num = POSITION_LIMIT - cpos
            orders.append(Order("STARFRUIT", bid_pr, num))
            cpos += num

        cpos = position

        for bid, vol in obuy.items():
            if ((bid >= our_ask) or ((position>0) and (bid+1 == our_ask))) and cpos > -POSITION_LIMIT:
                order_for = max(-vol, -POSITION_LIMIT-cpos) # order_for is a negative number denoting how much we will sell
                cpos += order_for
                orders.append(Order("STARFRUIT", bid, order_for))

        if cpos > -POSITION_LIMIT:
            num = -POSITION_LIMIT-cpos
            orders.append(Order("STARFRUIT", sell_pr, num))
            cpos += num

        return orders

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        orders = {}
        conversions = 0

        if state.traderData == '':
            traderData = {"STARFRUIT": {"slow_ema": None, "fast_ema": None}}
        else:
            traderData = json.loads(state.traderData)

        product = "AMETHYSTS"
        position = state.position.get(product, 0)
        order_depth: OrderDepth = state.order_depths[product] 
        orders[product] = self.compute_amethysts_order(position, order_depth, 10000)

        product = "STARFRUIT"
        position = state.position.get(product, 0)
        order_depth: OrderDepth = state.order_depths[product]
        midprice = self.compute_midprice(order_depth)
        slow_ema = self.compute_ema(midprice, previous_ema = traderData[product]["slow_ema"], alpha=0.01)
        traderData[product]["slow_ema"] = slow_ema
        fast_ema = self.compute_ema(midprice, previous_ema = traderData[product]["fast_ema"], alpha=0.1) 
        traderData[product]["fast_ema"] = fast_ema
        fair_value = self.compute_starfruit_value(midprice, slow_ema, fast_ema)
        orders[product] = self.compute_starfruit_order(position, order_depth, fair_value)
    
        traderData = json.dumps(traderData)
        logger.flush(state, orders, conversions, traderData)
        return orders, conversions, traderData
