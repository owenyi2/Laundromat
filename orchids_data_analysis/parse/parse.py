import pandas as pd
import re

log_file = "8cc2e28a-fdb7-45fa-b9a2-ead419ee94a4.log"
data_file = "58f05e45-8e35-4e8b-94b4-95c99f00368e.csv"

observations_data = []

for line in open(log_file).readlines():
    if "lambdaLog" in line:
        attributes = ["bidPrice", "askPrice", "transportFee", "exportTariff", "importTariff", "sunlight", "humidity"]        
        
        observation = {}

        observation["timestamp"] = int(re.findall(r"\[(\d*),", line)[0])
        for attribute in attributes:
            observation[attribute] = re.findall(rf"{attribute}.*?(\d.*?)[,}}]", line)[0]

        observations_data.append(observation)


observations_df = pd.DataFrame(observations_data)
print(observations_df)

orderbook_df = pd.read_csv(data_file, sep=";")
orderbook_df = orderbook_df[orderbook_df["product"] == "ORCHIDS"]
print(orderbook_df)

df = orderbook_df.merge(observations_df, on="timestamp")

df.to_csv("merged_data.csv")
