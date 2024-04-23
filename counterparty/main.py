import pandas as pd
import matplotlib.pyplot as plt

day = 2

round_3_trades_file = f"round-5-island-data-bottle/trades_round_3_day_{day}_wn.csv"
round_3_prices_file = f"round-3-island-data-bottle/prices_round_3_day_{day}.csv"

snakes = ["Remy", "Rhianna", "Ruby", "Vinnie", "Vladimir"]
products = ["ROSES", "CHOCOLATE", "STRAWBERRIES", "GIFT_BASKET"]

t_df = pd.read_csv(round_3_trades_file, sep=";")
p_df = pd.read_csv(round_3_prices_file, sep=";")

print(t_df)
print(p_df)

def analyse_product(product, trader, trades, prices, ax):
    t_df = trades[trades["symbol"] == product]
    p_df = prices[prices["product"] == product]
    
    buy = t_df[t_df["buyer"] == trader]
    sell = t_df[t_df["seller"] == trader]

    ax.plot(p_df["timestamp"], p_df["mid_price"])
    if len(buy) > 0:
        ax.scatter(buy["timestamp"], buy["price"], c="green")
    if len(sell) > 0: 
        ax.scatter(sell["timestamp"], sell["price"], c="red")
    ax.set_title(f'product: {product}, trader: {trader}')

def calculate_profit(product, trader, trades, final_prices):
    t_df = trades[(trades["symbol"] == product) & (trades["symbol"] == product)]

    buy = t_df[t_df["buyer"] == trader]
    sell = t_df[t_df["seller"] == trader]

    cash = (sell["quantity"] * sell["price"]).sum() - (buy["quantity"] * buy["price"]).sum()
    position = buy["quantity"].sum() - sell["quantity"].sum()

    final_price = final_prices[final_prices["product"] == product]["mid_price"].values[0]

    print(position)
    return cash + position * final_price

fig = plt.figure()

snakes = [snake for snake in snakes if (snake  not in ["Rhianna", "Ruby"])]
products = [product for product in products if (product not in ["ROSES", "GIFT_BASKET"])]

for i, snake in enumerate(snakes):
    for j, product in enumerate(products):
        pandl = calculate_profit(product, snake, t_df, p_df[p_df["timestamp"] == 999900])
        print(f"product: {product}, trader: {snake}, pandl: {pandl}")
        ax = fig.add_subplot(len(snakes), len(products), i * len(products) + j + 1)
        analyse_product(product, snake, t_df, p_df, ax)

plt.show()

# ok so basically invert Remy and Idk about Vladimir
