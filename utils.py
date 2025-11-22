import requests
import statistics as st
import pandas as pd
from imcity_template import BaseBot, Side, OrderRequest, OrderBook, Order
from typing import Tuple

def eisbach_value(flow_rate: float, water_level: float) -> float:
    """
    Settlement value for 1_Eisbach
    """
    return round(flow_rate*water_level)

def eisbach_call_value(strike_price: float, flow_rates: list[float], water_levels: list[float]) -> float:
    """
    Settlement value for 2_Eisbach_call
    """
    settlement_value = round((max(water_levels) * max(flow_rates)) - (min(water_levels) - min(flow_rates)))
    return max(0, settlement_value-strike_price)

def weather_3_value(temperatures: list[float]|pd.Series, humidities: list[float]|pd.Series) -> float:
    """
    Settlement value for 3_Weather
    """
    # Sanity check: Ensure we have pairs for every interval
    if len(temperatures) != len(humidities):
        raise ValueError("Temperature and Humidity lists must have the same length.")

    total_sum = 0
    # Iterate through both lists simultaneously
    for temp, humidity in zip(temperatures, humidities):
        # Calculate interval value: (Temperature * 2 + Humidity)
        total_sum += (temp * 2) + humidity
        # print(f'cumsum : {total_sum}')
        
    # TODO: get half-hourly data and remove *2
    return abs(total_sum)

def weather_4_value(temperatures: list[float]|pd.Series, humidities: list[float]|pd.Series) -> np.float:
    """
    Settlement value for 4_Weather
    """
    # Sanity check: Ensure we have pairs for every interval
    if len(temperatures) != len(humidities):
        raise ValueError("Temperature and Humidity lists must have the same length.")
    
    total_settlement = 0.0
    
    # Iterate through the data, index 'i' represents the current time step
    for i in range(len(temperatures)):
        # 1. Define the Window
        window_temps = temperatures[:i+1]
        window_hums = humidities[:i+1]
        
        # 2. Calculate Statistics for this window
        t_mean = st.mean(window_temps)
        t_median = st.median(window_temps)
        h_mean = st.mean(window_hums)
        h_median = st.median(window_hums)
        
        current_temp = temperatures[i]
        current_humidity = humidities[i]
        
        step_value = (current_temp+current_humidity) * ((t_mean - t_median) * (h_mean - h_median))
        
        # TODO: get half-hourly data and remove *2
        total_settlement += step_value

    # 4. Final Absolute Value
    return abs(total_settlement)

def flights_value(arrivals: list[int], departures: list[int]) -> float:
    """
    Settlement value for 5_Flights
    """
    return 3*(sum(arrivals)+sum(departures))

def airport_value(arrivals: list[int], departures: list[int]) -> float:
    """
    Settlement value for 6_Airport
    """
    total_metric_sum = 0.0
    
    for arr, dep in zip(arrivals, departures):
        # Safety check: If there are 0 flights, denominator becomes 0.
        # We assume 0 volume = 0 metric.
        if (arr + dep) == 0:
            continue
            
        numerator = arr - dep
        denominator = (arr + dep) ** 1.5

        interval_metric = 300 * (numerator / denominator)
        total_metric_sum += interval_metric

    final_settlement = round(abs(total_metric_sum))
    
    return final_settlement

def etf_value(flow_rate: float, water_level: float, latest_temp: float, latest_humidity: float, arrivals: list[int], departures: list[int]) -> float:
    """
    Settlement value for 7_ETF
    """
    return abs(0.3*flow_rate + 0.1*water_level + 0.2*latest_temp + 0.1*latest_humidity + 0.3*airport_value(arrivals, departures))

def etf_strangle_value(flow_rate: float, water_level: float, latest_temp: float, latest_humidity: float, arrivals: list[int], departures: list[int]) -> float:
    """
    TODO: AI generated, did not verify
    Settlement value for 8_ETF_Strangle
    """
    # 1. Calculate Put Payoff (Strike 80)
    # Formula: max(0, Strike - Underlying)
    put_payoff = max(0, 80 - etf_value(flow_rate, water_level, latest_temp, latest_humidity, arrivals, departures))
    
    # 2. Calculate Call Payoff (Strike 100)
    # Formula: max(0, Underlying - Strike)
    call_payoff = max(0, etf_value(flow_rate, water_level, latest_temp, latest_humidity, arrivals, departures) - 100)
    
    # 3. Total Settlement
    return put_payoff + call_payoff

def get_spread(recent_trades: pd.DataFrame) -> float:
    # compute the spread
    ask_trades = recent_trades[recent_trades['aggressor'] == recent_trades['buyer']]
    bid_trades = recent_trades[recent_trades['aggressor'] == recent_trades['seller']]

    # 2. Calculate the average price for each side
    avg_ask_price = ask_trades['price'].mean()
    avg_bid_price = bid_trades['price'].mean()

    # 3. Calculate the Spread
    if pd.notna(avg_ask_price) and pd.notna(avg_bid_price):
        average_spread = avg_ask_price - avg_bid_price
        print(f"Average Ask Price (Buy Aggressor): {avg_ask_price:.2f}")
        print(f"Average Bid Price (Sell Aggressor): {avg_bid_price:.2f}")
        print(f"Estimated Spread: {average_spread:.2f}")
    else:
        print("Not enough data to calculate spread (need both buy and sell aggressors in the window).")
    
    return average_spread

def get_most_traded_VWAP(exchange, username, password) -> Tuple[str, float, float]:
    class CustomBot(BaseBot):
        # Handler for own trades
        def on_trades(self, trades: list[dict]):
            for trade in trades:
                print(f"{trade['volume']} @ {trade['price']}")

        # Handler for order book updates
        def on_orderbook(self, orderbook: OrderBook):
            ...


    bot = CustomBot(exchange, username, password)

    response = requests.get(
        f"{exchange}/api/trade", headers=bot._get_headers()
    )
    trades = response.json()
    df = pd.DataFrame(trades)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 2. Define the time window
    latest_time = df['timestamp'].max()
    timedelta = 5
    start_time = latest_time - pd.Timedelta(minutes=timedelta)

    recent_trades = df[df['timestamp'] >= start_time]

    if not recent_trades.empty:
        # 2. Group by product and sum the volume
        # .idxmax() returns the index (product name) with the highest value
        most_traded_product = recent_trades.groupby('product')['volume'].sum().idxmax()

        # Optional: Get the actual volume number too
        total_vol = recent_trades.groupby('product')['volume'].sum().max()

        print(f"Most traded product: {most_traded_product} (Volume: {total_vol})")
    else:
        print("No trades in the timeframe.")

    recent_trades = recent_trades[recent_trades['product'] == most_traded_product]

    spread = get_spread(recent_trades)

    # Calculate VWAP
    target_product = most_traded_product
    if not recent_trades.empty:
        total_value = (recent_trades['price'] * recent_trades['volume']).sum()
        total_volume = recent_trades['volume'].sum()

        # Avoid division by zero if volume is 0
        if total_volume > 0:
            vwap = total_value / total_volume
            print(f"VWAP for {target_product} (Last {timedelta} Mins): {vwap:.2f}")
            print(f"Based on {len(recent_trades)} trades from {start_time.time()} to {latest_time.time()}")
        else:
            print("Total volume is 0.")
    else:
        print(f"No trades found for {target_product} in the last 10 minutes.")
        return None

    return most_traded_product, vwap, spread
    