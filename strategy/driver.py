import pandas as pd
import numpy as np
import json

from datamodel import OrderDepth, UserId, TradingState, Order, Listing

from amethyst_starfruit import Trader

df = pd.read_csv("activity.csv", sep=";", skiprows=1)

listings = {
	"AMETHYSTS": Listing(
		symbol="AMETHYSTS", 
		product="AMETHYSTS", 
		denomination= "SEASHELLS"
	),
	"STARFRUIT": Listing(
		symbol="STARFRUIT", 
		product="STARFRUIT", 
		denomination= "SEASHELLS"
	),
}

positions = {"AMETHYSTS": 0, "STARFRUIT": 0}

state = TradingState(
    traderData = "",
    timestamp = 0,
    listings = listings,
    order_depths = dict(),
    own_trades = "",
    market_trades = "",
    position = positions,
    observations = "",
)

previous_timestamp = 0

order_depths = {"AMETHYSTS": None, "STARFRUIT": None} 

trader = Trader()

for idx, row in df.iterrows():
    if row.timestamp != previous_timestamp: 
        previous_timestamp = row.timestamp
        result, conversions, traderData = trader.run(state)        

        print(result)
        state.traderData = traderData


    else:
        order_depth = OrderDepth()
        for price, volume in [(row.bid_price_1, row.bid_volume_1), (row.bid_price_2, row.bid_volume_2), (row.bid_price_3, row.bid_volume_3)]:
            if np.isnan(price):
                break
            order_depth.buy_orders[price] = volume


        for price, volume in [(row.ask_price_1, row.ask_volume_1), (row.ask_price_2, row.ask_volume_2), (row.ask_price_3, row.ask_volume_3)]:
            if np.isnan(price):
                break
            order_depth.sell_orders[price] = -volume
        

        state.order_depths[row["product"]] = order_depth
        state.timestamp = row.timestamp

        



        
