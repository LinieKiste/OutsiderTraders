from imcity_template import BaseBot, Side, OrderRequest, OrderBook, Order

import time
import pandas as pd
import requests
import json

TEST_EXCHANGE = "http://ec2-52-31-108-187.eu-west-1.compute.amazonaws.com"  # TODO
REAL_EXCHANGE = "http://ec2-18-203-201-148.eu-west-1.compute.amazonaws.com"  # TODO

username = (
    "OutsiderTraders"  # TODO: Change this to your team's username you've created in CMI
)
password = "something simple"  # TODO: Change this to be your team's password you've created in CMI


class CustomBot(BaseBot):

    # Handler for own trades
    def on_trades(self, trades: list[dict]):
        for trade in trades:
            print(f"{trade['volume']} @ {trade['price']}")

    # Handler for order book updates
    def on_orderbook(self, orderbook: OrderBook):
        current_time = time.time()
        file = orderbook.product
        df = pd.read_csv(file, header=None)
        print(df)
        time.sleep(0.3)
        # df = df[df[0] >= current_time - 300]
        if orderbook.buy_orders[0] > df[2].max() * 1.05:
            print(f"SELL {file}")
        elif orderbook.sell_orders[0] < df[1].min() / 1.05:
            print(f"BUY {file}")
        with open(f"{file}", "a") as myfile:
            myfile.write(
                f"{current_time}, {orderbook.buy_orders[0].price}, {orderbook.sell_orders[0].price}\n"
            )
            myfile.flush()


def main(product, buy_price, sell_price):
    current_time = time.time()
    file = product
    df = pd.read_csv(file, header=None)
    df = df[df[0] >= current_time - 300]
    if buy_price > df[2].max() * 1.05:
        print(f"SELL {file}")
    elif sell_price < df[1].min() / 1.05:
        print(f"BUY {file}")
    with open(f"{file}", "a") as myfile:
        myfile.write(f"{current_time}, {buy_price}, {sell_price}\n")
        myfile.flush()


bot = CustomBot(REAL_EXCHANGE, username, password)

try:
    while True:
        time.sleep(8)
        for market in [
            "1_Eisbach",
            "2_Eisbach_Call",
            "3_Weather",
            "7_ETF",
            "8_ETF_Strangle",
            "5_Flights",
            "4_Weather",
            "6_Airport",
        ]:
            response = requests.get(
                f"{REAL_EXCHANGE}/api/product/{market}/order-book/current-user?sessionId=CRAB",
                headers=bot._get_headers(),
            )
            main(
                market,
                json.loads(response.text)["buy"][0]["price"],
                json.loads(response.text)["sell"][0]["price"],
            )
except KeyboardInterrupt:
    pass
