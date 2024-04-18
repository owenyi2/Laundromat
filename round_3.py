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
        
        best_sell_pr = min(filter(lambda x: x > fair_value, osell.keys()))
        best_buy_pr = max(filter(lambda x: x < fair_value, obuy.keys()))

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

    def compute_starfruit_fair_value(self, best_bid, best_ask):
        bid_gain = .5
        ask_gain = .5 
        threshold = 1

        if self.traderData["STARFRUIT"]["adjusted_bid"] is None:
            adjusted_bid = best_bid
        else:
            previous_adjusted_bid = self.traderData["STARFRUIT"]["adjusted_bid"]
            previous_bid = self.traderData["STARFRUIT"]["previous_bid"]
            adjusted_bid = (previous_adjusted_bid + previous_bid * bid_gain) / (1 + bid_gain)
        
        if best_bid >= adjusted_bid + threshold:
            self.traderData["STARFRUIT"]["adjusted_bid"] = adjusted_bid
        else:
            self.traderData["STARFRUIT"]["adjusted_bid"] = best_bid
        self.traderData["STARFRUIT"]["previous_bid"] = best_bid

        if self.traderData["STARFRUIT"]["adjusted_ask"] is None:
            adjusted_ask = best_ask
        else:
            previous_adjusted_ask = self.traderData["STARFRUIT"]["adjusted_ask"]
            previous_ask = self.traderData["STARFRUIT"]["previous_ask"]
            adjusted_ask = (previous_adjusted_ask + previous_ask * ask_gain) / (1 + ask_gain)

        if best_ask <= adjusted_ask - threshold:
            self.traderData["STARFRUIT"]["adjusted_ask"] = adjusted_ask
        else:
            self.traderData["STARFRUIT"]["adjusted_ask"] = best_ask
        self.traderData["STARFRUIT"]["previous_ask"] = best_ask
        
        fair_price = (self.traderData["STARFRUIT"]["adjusted_ask"] + self.traderData["STARFRUIT"]["adjusted_bid"]) / 2.0 
       
        return int(round(fair_price))

    def compute_starfruit_order(self, state: TradingState) -> list[Order]:
        position = state.position.get("STARFRUIT", 0)
        order_depth: OrderDepth = state.order_depths["STARFRUIT"] 

        orders: list[Order] = []
        POSITION_LIMIT = 20

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))
    
        best_ask_pr = min(osell.keys())
        best_bid_pr = max(obuy.keys())
 
        midprice = (best_ask_pr + best_bid_pr) / 2.0
        fair_value = self.compute_starfruit_fair_value(best_bid_pr, best_ask_pr)

        logger.print(f"fair,{fair_value}")
        logger.print(f"midprice,{midprice}")

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
        
        best_sell_pr = min(filter(lambda x: x > fair_value, osell.keys()))
        best_buy_pr = max(filter(lambda x: x < fair_value, obuy.keys()))

        bid_pr = min(best_bid_pr + 1, our_bid) # we will shift this by 1 to beat this price
        sell_pr = max(best_ask_pr - 1, our_ask)

        # SUBMIT BUY ORDERS
        cpos = position
        
        for ask, vol in osell.items(): 
            if ((ask < fair_value) or ((position < 0) and (ask == fair_value))) and cpos < POSITION_LIMIT:
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
            if ((bid > fair_value) or ((position > 0) and (bid == fair_value))) and cpos > -POSITION_LIMIT:
                order_for = max(-vol, -POSITION_LIMIT-cpos)
                cpos += order_for
                orders.append(Order("STARFRUIT", bid, order_for))

        if cpos > -POSITION_LIMIT:
            num = -POSITION_LIMIT-cpos
            orders.append(Order("STARFRUIT", sell_pr, num))
            cpos += num

        return orders 
    def handle_orchids(self, state: TradingState): 
        position = state.position.get("ORCHIDS", 0)
        order_depth: OrderDepth = state.order_depths["ORCHIDS"]
        orders: list[Order] = []
        conversion: int = 0

        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        observation: Observation = state.observations.conversionObservations["ORCHIDS"]

        POSITION_LIMIT = 100
        
        cpos = position

        sun_indicator = 10 * (observation.sunlight - 1000) / 2500 
        humidity = observation.humidity
        previous_humidity = self.traderData["ORCHIDS"]["previous_humidity"]

        logger.print("sun_indicator", sun_indicator)
        logger.print("humidity", humidity)
        logger.print("previous_humidity", previous_humidity)

        if sun_indicator + humidity > 100:
            bid, vol = next(iter(obuy.items()))
            order_for = max(-vol, -POSITION_LIMIT - cpos)
            cpos += order_for
            orders.append(Order("ORCHIDS", bid, order_for))
        
        if observation.humidity < 75 and humidity - previous_humidity > 0:
            conversion = -cpos

        self.traderData["ORCHIDS"]["previous_humidity"] = humidity

        return orders, conversion
    
    def wma(self, data_cache):
        data = np.array(data_cache)
        weights = np.arange(len(data)) + 1
    
        return np.dot(data, weights) / weights.sum()

    def basket_dma(self, value):        
        emaLength = 80
        emaGainLimit = 50
        hullPeriod = 28
        
        halfHullPeriod = int(round(hullPeriod * 0.5))
        rootHullPeriod = int(round(hullPeriod ** 0.5))
        alpha = 2.0 / (emaLength + 1)

        cache = self.traderData["GIFT_BASKET"]["cache"]
        cache.append(value)
        cache = cache[-halfHullPeriod:]

        wma1 = self.wma(cache[-halfHullPeriod:])
        wma2 = self.wma(cache[-hullPeriod:])
        raw_hma = (2*wma1) - wma2

        raw_hma_cache = self.traderData["GIFT_BASKET"]["raw_hma_cache"]
        raw_hma_cache.append(raw_hma)
        raw_hma_cache = raw_hma_cache[-rootHullPeriod:]
        hma = self.wma(raw_hma_cache)

        ema_previous = self.traderData["GIFT_BASKET"]["ema_previous"]
        ec_previous = self.traderData["GIFT_BASKET"]["ec_previous"]

        if ema_previous is None:
            ema_previous = value
        if ec_previous is None:
            ec_previous = value

        ema = alpha * value + (1-alpha) * ema_previous
        leastError = float("inf")

        for value1 in range(-emaGainLimit, emaGainLimit + 1):
            gain = value1 / 10
            ec = alpha * (ema + gain*(value-ec_previous)) + (1-alpha) * ec_previous
            error = value - ec
            if abs(error) < leastError:
                leastError = abs(error)
                bestGain = gain

        ec = alpha * (ema + bestGain * (value - ec_previous)) + (1-alpha) * ec_previous
        dma = (ec + hma) * 0.5
        
        self.traderData["GIFT_BASKET"]["cache"] = cache
        self.traderData["GIFT_BASKET"]["raw_hma_cache"] = raw_hma_cache
        self.traderData["GIFT_BASKET"]["ema_previous"] = ema
        self.traderData["GIFT_BASKET"]["ec_previous"] = ec

        return dma

    def handle_baskets(self, state: TradingState):
        positions = {}
        osell = {}
        obuy = {}
        midprice = {}

        composition = {"GIFT_BASKET": 1, "CHOCOLATE": -4, "STRAWBERRIES": -6, "ROSES": -1}

        POSITION_LIMIT = 58 # min(60, 250 / 4, 350 / 6, 60)
        for product in ["GIFT_BASKET", "CHOCOLATE", "STRAWBERRIES", "ROSES"]:
            positions[product] = state.position.get(product, 0)
            order_depth = state.order_depths[product]
            osell[product] = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
            obuy[product] = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))
            
            best_ask_pr = min(osell[product].keys())
            best_bid_pr = max(obuy[product].keys())
        
            midprice[product] = (best_ask_pr + best_bid_pr) / 2
        
        synthetic_price = midprice["GIFT_BASKET"] - 4 * midprice["CHOCOLATE"] - 6 * midprice["STRAWBERRIES"] - midprice["ROSES"]
        z_score = (synthetic_price - 385) /  71.1290 
       
       
        z_score_smooth = self.basket_dma(z_score)

        forecast = -np.clip(z_score_smooth, -1, 1)

        desired_position = forecast * POSITION_LIMIT
        current_position = positions["GIFT_BASKET"]

        logger.print("desired_position", desired_position)
        logger.print("current_position", current_position)
        logger.print("z_score", z_score)
        logger.print("z_score_smooth", z_score_smooth)
        logger.print("synthetic_price", synthetic_price)

        if desired_position > current_position and abs(current_position / desired_position - 1) > 0.1:
            # buy basket sell constituents
            order_vol = 1e9
            product_price = {}

            product_price["GIFT_BASKET"], vol = next(iter(osell["GIFT_BASKET"].items()))
            order_vol = min(-vol, order_vol)

            for product in ["CHOCOLATE", "STRAWBERRIES", "ROSES"]:
                product_price[product], vol = next(iter(obuy[product].items()))
                order_vol = min(order_vol, int(vol / -composition[product]))

            order_vol = min(order_vol, int(desired_position - current_position))
           
            orders = []
            for product in ["GIFT_BASKET", "CHOCOLATE", "STRAWBERRIES", "ROSES"]:
                orders.append([Order(product, product_price[product], order_vol * composition[product])])
            
            # return tuple(orders)
            return orders[0], [], [], []

        elif desired_position < current_position * 1.1 and abs(current_position / desired_position - 1) > 0.1:
            # sell basket buy constituents
            order_vol = 1e9
            product_price = {}

            product_price["GIFT_BASKET"], vol = next(iter(obuy["GIFT_BASKET"].items()))
            order_vol = min(vol, order_vol)

            for product in ["CHOCOLATE", "STRAWBERRIES", "ROSES"]:
                product_price[product], vol = next(iter(osell[product].items()))
                order_vol = min(order_vol, int(-vol / -composition[product]))

            order_vol = min(order_vol, int(current_position - desired_position))
           
            orders = []
            for product in ["GIFT_BASKET", "CHOCOLATE", "STRAWBERRIES", "ROSES"]:
                orders.append([Order(product, product_price[product], -order_vol * composition[product])])
            # return tuple(orders)
            return orders[0], [], [], []
        else:
            return [], [], [], []

    def parse_trader_data(self, state: TradingState):
        if state.traderData == '':
            self.traderData = {"STARFRUIT": {"previous_ask": None, "adjusted_ask": None, "adjusted_bid": None, "previous_bid": None}, "ORCHIDS": {"previous_humidity": None}, "GIFT_BASKET": {"ema_previous": None, "ec_previous": None, "cache": [], "raw_hma_cache": []}}
        else:
            self.traderData = json.loads(state.traderData) 

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        orders = {}
        conversions = 0

        self.parse_trader_data(state)
        orders["AMETHYSTS"] = self.compute_amethysts_order(state)
        orders["STARFRUIT"] = self.compute_starfruit_order(state) 
        orders["ORCHIDS"], conversions = self.handle_orchids(state) 
        orders["GIFT_BASKET"], orders["CHOCOLATE"], orders["STRAWBERRIES"], orders["ROSES"] = self.handle_baskets(state) 

        traderData = json.dumps(self.traderData)
        logger.flush(state, orders, conversions, traderData)
        return orders, conversions, traderData
