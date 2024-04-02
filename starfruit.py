from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

import numpy as np

class Trader: 
    def run(self, state: TradingState):
        print("<state>" + state.toJSON() + "</state>")
            
        max_look_back = 49
        look_forward = 10

        STARFRUIT_LIMIT = 20

        result = {}
        for product in state.order_depths:
            if product == "AMETHYSTS":
                continue

            order_depth: OrderDepth = state.order_depths[product]
            mid_price = None 

            if len(order_depth.sell_orders) != 0 and len(order_depth.buy_orders) != 0:
                best_ask, _ = list(order_depth.sell_orders.items())[0]
                best_bid, _ = list(order_depth.buy_orders.items())[0]

                mid_price = (best_ask + best_bid) / 2.0
            
            historical_prices = []

            if state.traderData != '':
                historical_prices = state.traderData.split(",")
                historical_prices = [float(p) for p in historical_prices][-max_look_back:]
            
            historical_prices.append(mid_price)

            x = np.arange(len(historical_prices))
            y = np.array(historical_prices)

            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            
            acceptable_price = m * (len(historical_prices) + look_forward) + c

            orders: List[Order] = [] 


            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
    
    
        traderData = ",".join([str(p) for p in historical_prices])
        
        conversions = 1
        return result, conversions, traderData
