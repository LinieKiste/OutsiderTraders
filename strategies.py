from imcity_template import BaseBot, Side, OrderRequest, OrderBook, Order

import openmeteo_requests
import requests
from typing import Literal
from datetime import datetime, timedelta
import pandas as pd
import requests_cache
from retry_requests import retry

import OutsiderTraders.utils as utils

def fetch_weather_values(start: datetime = datetime(2025, 11, 22, 10), end: datetime = datetime(2025, 11, 23, 10)):
	# 1. API Call (Added timezone=Europe/Berlin to match Munich time)
	# url = "https://api.open-meteo.com/v1/forecast?latitude=48.1374&longitude=11.5755&hourly=temperature_2m,relative_humidity_2m&current=temperature_2m,relative_humidity_2m&past_days=1&forecast_days=3&temperature_unit=fahrenheit"
	# Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
    	"latitude": 48.1374,
    	"longitude": 11.5755,
    	"hourly": ["temperature_2m", "relative_humidity_2m"],
    	"current": ["temperature_2m", "relative_humidity_2m"],
    	"past_days": 1,
    	"forecast_days": 3,
    	"temperature_unit": "fahrenheit",
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # 2. Create DataFrame directly from the 'hourly' dictionary
    # The dictionary looks like: {'time': [...], 'temperature_2m': [...], ...}
    hourly = response.Hourly()

    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_data = {"date": pd.date_range(
    		start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    	end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = hourly.Interval()),
    	inclusive = "left"
    )}
    hourly_data["temperature"] = hourly_temperature_2m
    hourly_data["humidity"] = hourly_relative_humidity_2m

    df = pd.DataFrame(data = hourly_data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.index = df.index.tz_localize(None)

	# 5. Filter using the Time Index (Inclusive)
    filtered_df = df.loc[start:end]
    return filtered_df

def predict_weather_3_value(start: datetime = datetime(2025, 11, 22, 10), end: datetime = datetime(2025, 11, 23, 10)):
    filtered_df = fetch_weather_values(start, end)
    val = utils.weather_3_value(filtered_df['temperature'], filtered_df['humidity'])
    return val

def predict_weather_4_value(start: datetime = datetime(2025, 11, 22, 10), end: datetime = datetime(2025, 11, 23, 10)):
    filtered_df = fetch_weather_values(start, end)
    val = utils.weather_4_value(filtered_df['temperature'], filtered_df['humidity'])
    return val

def strategy(orderbook: OrderBook) -> Literal["buy", "sell", "hold"]:
    if orderbook.product == "3_Weather":
        val = predict_weather_3_value(datetime(2025, 11, 22, 10), datetime(2025, 11, 23, 10))
        val -= 800
        best_bid = orderbook.sell_orders[0].price
        best_ask = orderbook.buy_orders[0].price
        print(val)
        if best_bid + 200 < val:
            print("BUY WEATHER")
            return "buy"
        if best_ask - 200 > val:
            print("SELL WEATHER")
            return "sell"
        print("HOLD WEATHER")
        return "hold"
    if orderbook.product == "4_Weather":
        val = predict_weather_4_value(datetime(2025, 11, 21, 9), datetime(2025, 11, 22, 8))
        best_bid = orderbook.sell_orders[0].price
        best_ask = orderbook.buy_orders[0].price
        print(val)
    return 'hold'
#         if best_bid + 200 < val:
#             print("BUY WEATHER")
#             return "buy"
#         if best_ask - 200 > val:
#             print("SELL WEATHER")
#             return "sell"
#         print("HOLD WEATHER")
#         return "hold"

if __name__ == "__main__":
    val = predict_weather_3_value(datetime(2025, 11, 21, 9), datetime(2025, 11, 22, 9))
    print(val)