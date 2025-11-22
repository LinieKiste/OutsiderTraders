import statistics as st

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

def weather_3_value(temperatures: list[float], humidities: list[float]) -> float:
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
        
    # The rule states: "settles to absolute value of outcome"
    return abs(total_sum)

def weather_4_value(temperatures: list[float], humidities: list[float]) -> float:
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
        
        step_value = current_temp * (t_mean - t_median) * (h_mean - h_median)
        
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