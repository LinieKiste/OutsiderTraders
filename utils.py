import statistics as st
import pandas as pd
import requests


def eisbach_value(flow_rate: float, water_level: float) -> float:
    """
    Settlement value for 1_Eisbach
    """

    url_abfluss = "https://www.hnd.bayern.de/pegel/isar/muenchen-himmelreichbruecke-16515005/tabelle?methode=abfluss&setdiskr=15"
    url_stand = "https://www.hnd.bayern.de/pegel/isar/muenchen-himmelreichbruecke-16515005/tabelle?methode=wasserstand&setdiskr=15"
    a = requests.get(url_abfluss).content

    standdf = pd.read_html(
        requests.get(url_stand).content, decimal=",", thousands=".", parse_dates=True
    )[-1]

    abflussdf = pd.read_html(a, decimal=",", thousands=".", parse_dates=True)[-1]

    current_abfluss = abflussdf.iloc[0]["Abfluss m³/s"]
    stand = standdf.iloc[0]["Wasserstand cm über Pegelnullpunkt (506,06 m NHN)"]
    last_date = pd.read_html(a, decimal=",", thousands=".", parse_dates=True)[-1].iloc[
        0
    ]["Datum"]

    return round(current_abfluss * stand)


def eisbach_call_value(
    strike_price: float, flow_rates: list[float], water_levels: list[float]
) -> float:
    """
    Settlement value for 2_Eisbach_call
    """
    url_abfluss = "https://www.hnd.bayern.de/pegel/isar/muenchen-himmelreichbruecke-16515005/tabelle?methode=abfluss&setdiskr=15"

    url_stand = "https://www.hnd.bayern.de/pegel/isar/muenchen-himmelreichbruecke-16515005/tabelle?methode=wasserstand&setdiskr=15"
    a = requests.get(url_abfluss).content

    standdf = pd.read_html(
        requests.get(url_stand).content, decimal=",", thousands=".", parse_dates=True
    )[-1]

    abflussdf = pd.read_html(a, decimal=",", thousands=".", parse_dates=True)[-1]

    last_date = pd.read_html(a, decimal=",", thousands=".", parse_dates=True)[-1].iloc[
        0
    ]["Datum"]

    if int(last_date[1]) == 2:
        hour = int(last_date[11:13])
        i = (hour - 10) * 4
    if int(last_date[1]) == 3:
        hour = int(last_date[11:13])
        i = (hour + 14) * 4
    if int(last_date[15]) == 5:
        i = i + 1
    if int(last_date[14]) == 3 or int(last_date[14]) == 4:
        i = i + 2

    # i = 24 * 4

    max_ab = 0
    max_stand = 0
    min_ab = 99999999
    min_stand = 99999999

    for i in range(0, i):
        if (
            standdf.iloc[i]["Wasserstand cm über Pegelnullpunkt (506,06 m NHN)"]
            < min_stand
        ):
            min_stand = standdf.iloc[i][
                "Wasserstand cm über Pegelnullpunkt (506,06 m NHN)"
            ]
        if (
            standdf.iloc[i]["Wasserstand cm über Pegelnullpunkt (506,06 m NHN)"]
            > max_stand
        ):
            max_stand = standdf.iloc[i][
                "Wasserstand cm über Pegelnullpunkt (506,06 m NHN)"
            ]
        if abflussdf.iloc[i]["Abfluss m³/s"] < min_ab:
            min_ab = abflussdf.iloc[i]["Abfluss m³/s"]
        if abflussdf.iloc[i]["Abfluss m³/s"] > max_ab:
            max_ab = abflussdf.iloc[i]["Abfluss m³/s"]

    return (max_stand - max_ab) * (min_stand - min_ab) - 5000


def weather_3_value(
    temperatures: list[float] | pd.Series, humidities: list[float] | pd.Series
) -> float:
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
    return abs(total_sum * 2)


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
        window_temps = temperatures[: i + 1]
        window_hums = humidities[: i + 1]

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
    return 3 * (sum(arrivals) + sum(departures))


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


def etf_value(
    flow_rate: float,
    water_level: float,
    latest_temp: float,
    latest_humidity: float,
    arrivals: list[int],
    departures: list[int],
) -> float:
    """
    Settlement value for 7_ETF
    """
    return abs(
        0.3 * flow_rate
        + 0.1 * water_level
        + 0.2 * latest_temp
        + 0.1 * latest_humidity
        + 0.3 * airport_value(arrivals, departures)
    )


def etf_strangle_value(
    flow_rate: float,
    water_level: float,
    latest_temp: float,
    latest_humidity: float,
    arrivals: list[int],
    departures: list[int],
) -> float:
    """
    TODO: AI generated, did not verify
    Settlement value for 8_ETF_Strangle
    """
    # 1. Calculate Put Payoff (Strike 80)
    # Formula: max(0, Strike - Underlying)
    put_payoff = max(
        0,
        80
        - etf_value(
            flow_rate, water_level, latest_temp, latest_humidity, arrivals, departures
        ),
    )

    # 2. Calculate Call Payoff (Strike 100)
    # Formula: max(0, Underlying - Strike)
    call_payoff = max(
        0,
        etf_value(
            flow_rate, water_level, latest_temp, latest_humidity, arrivals, departures
        )
        - 100,
    )

    # 3. Total Settlement
    return put_payoff + call_payoff
