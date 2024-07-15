"""
    Filename: utils.py
     Version: 1.0
      Author: Richard E. Rawson
        Date: 2024-06-28
 Description: Utility functions for weather.py

"""

import atexit
import configparser
import json
import os
from random import randint

import pandas as pd
import requests
import utilities.r_utils as ru
from icecream import ic
from meteostat import Stations
from rich import print
from utilities import rdatetime as rd

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY: str = config['DEFAULT']['API_KEY']
DEFAULT_LAT: str = config['DEFAULT']['DEFAULT_LAT']
DEFAULT_LON: str = config['DEFAULT']['DEFAULT_LON']
DEFAULT_CITY: str = config['DEFAULT']['DEFAULT_CITY']
DEFAULT_STATE: str = config['DEFAULT']['DEFAULT_STATE']

# Create a naive date string for today's date in YYYY-MM-DD format.
todaydatetime: rd.datetime = rd.datetime.now()
todaynaive: rd.datetime = rd.tzdatetime_to_naivedatetime(todaydatetime)
TODAYS_DATE: str = rd.datetime_to_datestr(todaynaive, fmt="%Y-%m-%d")


def get_weather_report(period, latitude, longitude, city, state, days) -> None:
    """
    This function is used by both the "coords" and "location" arguments to download, extract, and print the current or forecasted weather.

    Parameters
    ----------
    period : str -- either "current" weather or "forecast"; "current" is default
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    """

    if period == 'current':
        # Download the current weather data.
        data = get_current_data(latitude, longitude)

        # try:
        #     if data['alerts'][0]['sender_name']:
        #         alerts = data["alerts"][0]
        # except KeyError:
        #     alerts = ""

        # From the downloaded weather data, extract just the variables we want.
        date, weather, feels_like, humidity, pressure, temperature, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow = extract_current_weather_vars(data)

        # Print a final report for the current weather.
        print_current_weather(city, state, latitude, longitude, date, weather, feels_like, humidity, pressure, temperature, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow, data)

    else:
        # Download the forecast data.
        data = get_forecast_data(latitude, longitude)

        # Extract just the variables we want from the downloaded data.
        forecast: list[list[str]] = extract_forecast_vars(data)

        # Print the final report for forecasted weather.
        print_forecast(city, state, forecast[:days], data)


# ==== DOWNLOAD DATA =========================================================

"""
    These functions delimit the extent of data downloaded from openweathermap.org. All of these functions download from that site. "meteostat" commands download data from "meteostat.net" and those download functions are included in each "meteostat" command.
"""


def download_data(latitude, longitude, filter_times) -> dict:
    """
    Download data from openweathermap.org. Using "filtered_time" the downloaded data contains only the information required by the calling function.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    filter_times : str -- the categories of periods to be excluded from download

    Returns
    -------
    dict -- json data downloaded
    """

    url: str = f'https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&units=imperial&exclude={filter_times}&appid={API_KEY}'

    r = requests.get(url)
    if r.status_code != 200:
        print('\nCould not reach "https://api.openweathermap.org".', sep="")
        exit()

    data = r.json()

    # ! I don't tkink there's any good reason to save these data.
    # save_data(data)

    return data


def get_current_data(latitude: float, longitude: float) -> dict:
    """
    Download the current weather data from openweathermap.org.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest

    Returns
    -------
    dict -- downloaded json data
    """

    # "filter_times" are the periods to filter OUT.
    filter_times: str = "hourly,minutely,daily"
    return download_data(latitude, longitude, filter_times)


def get_forecast_data(latitude: float, longitude: float) -> dict:
    """
    Download the forecast data from openweathermap.org.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest

    Returns
    -------
    dict -- downloaded json data
    """

    # "filter_times" are the periods to filter OUT.
    filter_times: str = "current,minutely,hourly"
    return download_data(latitude, longitude, filter_times)


def get_hourly_forecast_data(latitude, longitude) -> dict:
    """
    Download data for the hourly forecast.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest

    Returns
    -------
    dict -- downloaded json data
    """

    # "filter_times" are the periods to filter OUT.
    filter_times: str = "current,minutely,daily,alerts"
    return download_data(latitude, longitude, filter_times)


def get_rain_forecast_data(latitude, longitude) -> dict:
    """
    Get the precipitation for the next n hours. 48 hours is the max; 8 hours is default.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest

    Returns
    -------
    dict -- downloaded json data
    """

    # "filter_times" are the periods to filter OUT.
    filter_times: str = "current,hourly,daily,alerts"
    return download_data(latitude, longitude, filter_times)


def get_single_day_data(latitude: float, longitude: float, timeStamp: int) -> dict:
    """
    Download the single_day weather data for the date and specific time (timestamp) provided.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    timeStamp : int -- integer timeStamp for date; timestamp is required by API

    Returns
    -------
    dict -- downloaded json data
    """

    url: str = f'https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={latitude}&lon={longitude}&units=imperial&dt={timeStamp}&appid={API_KEY}'

    r = requests.get(url)
    if r.status_code != 200:
        print('\nCould not reach "https://api.openweathermap.org".', sep="")
        exit()

    data = r.json()
    save_data(data)

    return data


# ==== EXTRACT NEEDED INFORMATION FROM DOWNLOADED DATA =======================
"""
    `NOTE:
    Explicit functions for current weather and forecast weather are needed
    since we need to extract a sizeable number of variables from the json
    data. For other reports, the number of variables is limited and so
    those "extractions" are handled by the click.command functions.
"""


def extract_current_weather_vars(data) -> tuple[str, str, float, int, float, float, int, str, float, str, str, float, float, float, float, float]:
    """
    From the downloaded data, extract just the values that we want. try...except blocks are required since some variables may not be present on some days.

    Parameters
    ----------
    data : dict -- the complete json data download from openweathermap.org

    Returns
    -------
    str, str, float, int, float, float, int, str, float, str, str, float, float, float, float, float -- weather data of interest
    """

    try:
        UTCdatetime: rd.datetime = rd.ts_to_datetime(data['current']['dt'])
        localdatetime: rd.datetime = rd.change_timezones(UTCdatetime, source_timezone='UTC')
        date = f'{rd.datetime_to_dow(localdatetime, length=-1)}, {localdatetime.strftime("%B %d, %Y, %I:%M %p")}'
    except KeyError:
        d = rd.datetime(year=1970, month=1, day=1, hour=12, minute=0, second=0)
        date: str = d.strftime('%Y-%m-%d %I:%M %p')
    try:
        weather = data['current']['weather'][0]['description']
    except KeyError:
        weather = ""
    try:
        feels_like = data['current']['feels_like']
    except KeyError:
        feels_like = 0.0
    try:
        humidity = data['current']['humidity']
    except KeyError:
        humidity = 0
    try:
        pressure: float = convert_pressure(data['current']['pressure'])
    except KeyError:
        pressure = 0.0
    try:
        temperature = data['current']['temp']
    except KeyError:
        temperature = 0.0
    try:
        visibility = data['current']['visibility']
    except KeyError:
        visibility = 0
    try:
        wind_direction = wind_direction_txt(data['current']['wind_deg'])
    except KeyError:
        wind_direction = "X"
    try:
        wind_speed = data['current']['wind_speed']
    except KeyError:
        wind_speed = 0.0
    try:
        sunrise: str = rd.ts_to_datestr(
            data['current']['sunrise'], fmt="%Y-%m-%d %I:%M %p")
    except KeyError:
        sunrise = "0.0"
    try:
        sunset: str = rd.ts_to_datestr(
            data['current']['sunset'], fmt="%Y-%m-%d %I:%M %p")
    except KeyError:
        sunset = "0.0"
    try:
        gust = data['current']['wind_gust']
    except KeyError:
        gust = 0.0
    try:
        uvi = data['current']['uvi']
    except KeyError:
        uvi = 0.0
    try:
        dew_point = data['current']['dew_point']
    except KeyError:
        dew_point = 0.0

    if "rain" in data["current"]:
        if isinstance(data['current']['rain'], dict):
            rain = data['current']['rain']['1h'] * 0.03937008
        if isinstance(data['current']['rain'], (int, float)):
            rain = data['current']['rain'] * 0.03937008
    else:
        rain = 0.0

    if "snow" in data["current"]:
        if isinstance(data['current']['snow'], dict):
            snow = data['current']['snow']['1h'] * 0.03937008
        if isinstance(data['current']['snow'], (int, float)):
            snow = data['current']['snow'] * 0.03937008
    else:
        snow = 0.0

    # print(type(date), type(weather), type(feels_like), type(humidity), type(pressure), type(temperature), type(visibility), type(wind_direction), type(wind_speed), type(sunrise), type(sunset), type(gust), type(uvi), type(dew_point), type(rain), type(snow))

    return date, weather, feels_like, humidity, pressure, temperature, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow


def extract_forecast_vars(data) -> list[list[str]]:
    """
    Given the raw json data downloaded from openweathermap.org, extract just the data that is needed for a concise 8-day forecast.

    Parameters
    ----------
    data : dict -- the complete json data download from openweathermap.org

    Returns
    -------
    list[list[str]] -- unformatted list of strings for 8-day forecasts

    Examples
    --------
    forecast: [['Today', 'Expect a day of partly cloudy with rain'],
               ['Sunday', 'Expect a day of partly cloudy with clear spells'],
               ...]
    """

    # "day" comprises all the date downloaded for a given day in the "daily"
    # portion of the downloaded data.
    forecast = []
    for day in data['daily']:
        daily: list[str] = []
        this_datetime: rd.datetime = rd.ts_to_datetime(day['dt'])
        this_datestr: str = rd.datetime_to_datestr(this_datetime)
        today_date: str = rd.datetime.strftime(rd.datetime.today(), "%Y-%m-%d")

        if this_datestr[0:10] == today_date:
            # daily.append("Today")
            daily.append(f'Today: {rd.datetime_to_dow(this_datetime)}, {this_datetime.strftime("%B %d")}')
        else:
            daily.append(this_datetime.strftime('%A'))

        daily = extract_daily_data(day, daily)

        forecast.append(daily)

    return forecast


def extract_daily_data(day, daily) -> list[str]:
    """
    Extract specific variables from the "daily" portion of the downloaded data.

    Parameters
    ----------
    day : dict -- all the "daily" data for one day
    daily : list -- contains only one element: today's date, formatted

    Returns
    -------
    list -- elements are all the extracted variables that we want to print
    """

    try:
        daily.append(day['summary'])
    except KeyError:
        daily.append("--")
    try:
        daily.append(day['temp']['min'])
    except KeyError:
        daily.append(0)
    try:
        daily.append(day['temp']['max'])
    except KeyError:
        daily.append(0)
    try:
        daily.append(day['humidity'])
    except KeyError:
        daily.append(0)
    try:
        daily.append(day['wind_speed'])
    except KeyError:
        daily.append(0)
    try:
        daily.append(day['pop'] * 100)
    except KeyError:
        daily.append(0)
    try:
        daily.append(day['rain'])
    except KeyError:
        daily.append(0)
    try:
        daily.append(day['snow'])
    except KeyError:
        daily.append(0)

    return daily


def extract_single_day_weather_vars(data) -> tuple[str, str, float, int, float, float, float, float, int, str, float, str, str, float, float, float, float, float]:
    """
    From the downloaded data, extract just the values that we want. try...except blocks are required since some variables may not be present on some days.

    Parameters
    ----------
    data : dict -- the complete json data download from openweathermap.org

    Returns
    -------
    str, str, float, int, float, float, float, float, int, str, float, str, str, float, float, float, float, float -- weather data of interest
    """

    try:
        localdatetime: rd.datetime = rd.ts_to_datetime(data['data'][0]['dt'])
        date: str = f'{rd.datetime_to_dow(localdatetime)}, {localdatetime.strftime("%B %d, %Y, %I:%M %p")}'
    except KeyError:
        d: rd.datetime = rd.datetime(
            year=1970, month=1, day=1, hour=12, minute=0, second=0)
        date: str = d.strftime('%Y-%m-%d %H:%M')
    try:
        weather = data['data'][0]['weather'][0]['description']
    except KeyError:
        weather = ""
    try:
        feels_like = data['data'][0]['feels_like']
    except KeyError:
        feels_like = 0.0
    try:
        humidity = data['data'][0]['humidity']
    except KeyError:
        humidity = 0
    try:
        pressure: float = convert_pressure(data['data'][0]['pressure'])
    except KeyError:
        pressure = 0.0
    try:
        temperature = data['data'][0]['temp']
    except KeyError:
        temperature = 0.0
    try:
        max_temp = data['data'][0]['temp_max']
    except KeyError:
        max_temp = 0.0
    try:
        min_temp = data['data'][0]['temp_min']
    except KeyError:
        min_temp = 0.0
    try:
        visibility = data['data'][0]['visibility']
    except KeyError:
        visibility = 0
    try:
        wind_direction = wind_direction_txt(data['data'][0]['wind_deg'])
    except KeyError:
        wind_direction = "X"
    try:
        wind_speed = data['data'][0]['wind_speed']
    except KeyError:
        wind_speed = 0.0
    try:
        sunrise: str = rd.ts_to_datestr(
            data['data'][0]['sunrise'], fmt="%I:%M %p")
    except KeyError:
        sunrise = "0.0"
    try:
        sunset: str = rd.ts_to_datestr(
            data['data'][0]['sunset'], fmt="%I:%M %p")
    except KeyError:
        sunset = "0.0"
    try:
        gust = data['data'][0]['wind_gust']
    except KeyError:
        gust = 0.0
    try:
        uvi = data['data'][0]['uvi']
    except KeyError:
        uvi = 0.0
    try:
        dew_point = data['data'][0]['dew_point']
    except KeyError:
        dew_point = 0.0
    try:
        rain = data['data'][0]['rain']["1h"]
    except KeyError:
        rain = 0.0
    try:
        snow = data['data'][0]['snow']["1h"]
    except KeyError:
        snow = 0.0

    # print(type(date), type(weather), type(feels_like), type(humidity), type(pressure), type(temperature), type(max_temp), type(min_temp), type(visibility), type(wind_direction), type(wind_speed), type(sunrise), type(sunset), type(gust), type(uvi), type(dew_point), type(rain), type(snow))

    return date, weather, feels_like, humidity, pressure, temperature, max_temp, min_temp, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow


# ==== FUNCTIONS TO PRINT WEATHER REPORTS ====================================
def print_current_weather(city, state, latitude, longitude, date, weather, feels_like, humidity, pressure, temperature, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow, data) -> None:
    """
    Print the current weather report.

    Example report:

    CURRENT WEATHER for
    Tuesday, March 26, 2024, 08:29 AM
    McNair, Virginia: 38.95669, -77.41006
            weather: broken clouds
        temperature: 35.9 °F
            feels like: 35.9 °F
            dew point: 30.0 °F
            humidity: 78%
            pressure: 575.0 mmHg / 22.6 ins
            UV index: 0.3 -- low
            visibility: 6.2 miles
        wind direction: west
            wind speed: 2.0 mph
                gust: 4.0
            sunrise: 07:02 AM
                sunset: 07:27 PM
    """

    pressure_mmhg: float = convert_pressure(pressure)
    visibility_miles: float = convert_visibility(visibility)

    print(f'\n[dark_orange]CURRENT WEATHER for\n{date}[/]', sep="")
    print(f'[italic underline dark_orange]{city}, {state}: {latitude}, {longitude}[/]', sep="")
    print(f'           [dark_orange]weather:[/] [light_steel_blue1]{weather}[/]', sep="")
    print(f'       [dark_orange]temperature:[/] [light_steel_blue1]{temperature:.1f} °F[/]')
    print(f'        [dark_orange]feels like:[/] [light_steel_blue1]{feels_like:.1f} °F[/]')
    print(f'         [dark_orange]dew point:[/] [light_steel_blue1]{dew_point:.1f} °F[/]')
    print(f'          [dark_orange]humidity:[/] [light_steel_blue1]{humidity:.0f}%[/]')
    inhg: float = pressure_mmhg * 0.03937
    print(f'          [dark_orange]pressure:[/] [light_steel_blue1]{pressure_mmhg:.1f} mmHg / {inhg:.1f} ins[/]')
    uvi_color, uv_text = get_uv_index_color(uvi)
    print(f'          [dark_orange]UV index:[/] [{uvi_color}]{uvi} -- {uv_text}[/]')
    print(f'        [dark_orange]visibility:[/] [light_steel_blue1]{visibility_miles:0.1f} miles[/]')
    if snow > 0.:
        print(f'              [dark_orange]snow:[/] [light_steel_blue1]{snow:0.2f} in.[/]')
    if rain > 0.:
        print(f'              [dark_orange]rain:[/] [light_steel_blue1]{rain:0.2f} in[/]')
    print(f'    [dark_orange]wind direction:[/] [light_steel_blue1]{wind_direction}[/]')
    print(f'        [dark_orange]wind speed:[/] [light_steel_blue1]{wind_speed:.1f} mph[/]')
    print(f'              [dark_orange]gust:[/] [light_steel_blue1]{gust:.1f}[/]')
    print(f'           [dark_orange]sunrise:[/] [light_steel_blue1]{sunrise[11:]}[/]')
    print(f'            [dark_orange]sunset:[/] [light_steel_blue1]{sunset[11:]}[/]')

    # Check to see if there actually is an alert:
    try:
        sender = data['alerts'][0]["sender_name"]
        print_alerts(city, state, data)
    except KeyError:
        print(f'\n[dark_orange]No alerts have been issued for[/] [#d6d9fe]{city}, {state}[/]', sep="")
        return None


def print_forecast(city, state, forecast: list[list[str]], data) -> None:
    """
    Print the 8-day forecast for the given city/state.

    Example report:

    FORECAST for McNair, Virginia
    Today: Tuesday, March 26:
    There will be partly cloudy today.
        Temperature low: 36 °F
    Temperature high: 58 °F
            Humidity: 53%
            Wind speed: 11 mph
        Chance of rain: 0%
    Expected rain fall: 0.00 in.
    Wednesday:
    Expect a day of partly cloudy with rain.
        Temperature low: 45 °F
    Temperature high: 51 °F
            Humidity: 93%
            Wind speed: 9 mph
        Chance of rain: 88%
    Expected rain fall: 0.04 in.

    Parameters
    ----------
    city : str -- city of interest
    state : str -- state of interest
    forecast : list[list[str]] -- _description_
    """

    print(f"\n[italic underline dark_orange]FORECAST for {city}, {state}[/]", sep="")

    for i in forecast:
        try:
            rain_amount: float = i[7] * 0.03937008
        except KeyError:
            rain_amount = 0.
        try:
            snow_amount: float = i[8] * 0.03937008
        except KeyError:
            snow_amount = 0.

        # day, summary, min, max, humidity, wind speed, pop, rain, snow
        print(f'[dark_orange]{i[0]}:[/]\n   [light_steel_blue1]{i[1]}[/].')
        print(f'    Temperature low: {i[2]:.0f} °F')
        print(f'   Temperature high: {i[3]:.0f} °F')
        print(f'           Humidity: {i[4]}%')
        print(f'         Wind speed: {i[5]:.0f} mph')
        print(f'     Chance of rain: {i[6]:.0f}%')
        print(f' Expected rain fall: {rain_amount:.2f} in.')
        if snow_amount > 0.:
            # If snow fall prints as 0.00, it's because there is an expectation of
            # snow, but very, very little.
            print(f' Expected snow fall: {snow_amount:.2f} in.')

    # Check to see if there actually is an alert:
    try:
        sender = data['alerts'][0]["sender_name"]
        print_alerts(city, state, data)
    except KeyError:
        print(f'\n[dark_orange]No alerts have been issued for[/] [#d6d9fe]{city}, {state}[/]', sep="")
        return None


def print_hourly_forecast(latitude, longitude, data, hours) -> None:
    """
    Print the precipitation forecast for the next "hours" hours. 8 hours is default; 48 hours is max.

    Example report:

    Hourly forecast for McNair, Virginia
    Tuesday, Mar 26, 2024
            08:00 AM                      09:00 AM
            broken clouds                 broken clouds
        Temperature: 37 °F            Temperature: 37 °F
               rain: 0.00 in.                rain: 0.00 in.
                UVI: 0.3                      UVI: 0.7
     Chance of rain: 0 %           Chance of rain: 0 %

    Parameters
    ----------
    data : dict -- downloaded json data
    hours : int -- the number of hours to report
    """
    hourly_forecast = data['hourly']
    current_datetime: rd.datetime = rd.ts_to_datetime(hourly_forecast[0]['dt'])
    current_localdatestr: str = rd.datetime_to_datestr(current_datetime, fmt="%A, %b %d, %Y")
    current_date: str = current_localdatestr

    city, state = get_location(latitude, longitude)

    print(f'\n[dark_orange]Hourly forecast for[/] [italic dark_orange]{city}, {state}[/]', sep="")
    print(f'[dark_orange]{current_date}[/]')

    # Put the data I need into a list[list[str]], where each internal list contains one hour's data.
    # For each hour, each list[str] will contain, h['dt'], h['temp'], h['uvi'], h['weather'][0]['description'], h['pop']
    # I then print 3 hours across.
    wlist = []
    for ndx, h in enumerate(hourly_forecast):
        if ndx + 1 > hours:
            break

        if "rain" in h:
            if isinstance(h['rain'], dict):
                rain = h['rain']['1h'] * 0.03937008
            if isinstance(h['rain'], (int, float)):
                rain = h['rain'] * 0.03937008
        else:
            rain = 0.0

        if "snow" in h:
            if isinstance(h['snow'], dict):
                snow = h['snow']['1h'] * 0.03937008
            if isinstance(h['snow'], (int, float)):
                snow = h['snow'] * 0.03937008
        else:
            snow = 0.0

        wlist.append([h['dt'], h['weather'][0]['description'], h['temp'], rain, snow, h['uvi'], h['pop']])

    for ndx in range(0, len(wlist), 3):
        try:
            for i in range(3):
                dt: str = rd.ts_to_datestr(wlist[ndx + i][0], fmt="%I:%M %p")
                print(f'[light_steel_blue1]{dt:^30}[/]', sep="", end="")
            print()
        except IndexError:
            print()
        try:
            for i in range(3):
                t: str = f'{wlist[ndx + i][1]}'
                print(f'[chartreuse1]{t:^30}[/]', sep="", end="")
            print()
        except IndexError:
            print()
        try:
            for i in range(3):
                t: str = f'     Temperature: {wlist[ndx + i][2]:.0f} °F'
                print(f'{t:<30}', sep="", end="")
            print()
        except IndexError:
            print()
        try:
            for i in range(3):
                t: str = f'            rain: {wlist[ndx + i][3]:.2f} in.'
                print(f'{t:<30}', sep="", end="")
            print()
        except IndexError:
            print()

        if snow > 0.0:
            try:
                for i in range(3):
                    t: str = f'            snow: {wlist[ndx + i][4]:.2f} in.'
                    print(f'{t:<30}', sep="", end="")
                print()
            except IndexError:
                print()
        try:
            for i in range(3):
                t: str = f'             UVI: {wlist[ndx + i][5]}'
                print(f'{t:<30}', sep="", end="")
            print()
        except IndexError:
            print()
        try:
            for i in range(3):
                t: str = f'  Chance of rain: {wlist[ndx + i][6] * 100:.0f} %'
                print(f'{t:<30}', sep="", end="")
            print()
        except IndexError:
            print()
        print()


def print_rain_forecast(latitude, longitude, data) -> None:
    """
    Print the rain forecast.

    Example report:

        Expected rainfall in the next hour
        2024-03-26 -- McNair, Virginia

        08:26: 0.00 in.
        08:31: 0.00 in.
        08:36: 0.00 in.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    data : dict -- "minutely" weather data
    """

    city, state = get_location(latitude, longitude)

    # Print the date and city/state
    forecast_date: str = rd.ts_to_datestr(data['minutely'][0]['dt'])
    print(f'[dark_orange]{forecast_date[:10]} -- [/]', end="")
    print(f'[italic dark_orange]{city}, {state}[/]')

    total_precip: float = 0.0

    # Print the hourly rainfall expectations at 5 min intervals.
    for i in range(0, len(data['minutely']), 5):
        precip = data['minutely'][i]['precipitation'] * 0.03937008
        total_precip += precip
        h: str = rd.ts_to_datestr(data['minutely'][i]['dt'], fmt="%Y-%m-%d %I:%M")
        print(f'{h[11:]}: {precip:.4f} in.')
    print(f'Total expected precipitation: {total_precip:0.4f} in.')


def print_alerts(city, state, data) -> None:
    """
    Print alerts, if any. A for... loop is used because it is conceivable that there can be more than one alert.

    Parameters
    ----------
    data : dict -- downloaded alerts data
    """
    print()

    for alert in data['alerts']:
        start_datetime: rd.datetime = rd.ts_to_datetime(
            alert['start'])
        start_datestr: str = rd.datetime_to_datestr(
            start_datetime, fmt="%Y-%m-%d %I:%M %p")
        end_datetime: rd.datetime = rd.ts_to_datetime(
            alert['end'])
        end_datestr: str = rd.datetime_to_datestr(
            end_datetime, fmt="%Y-%m-%d %I:%M %p")

        print(f'\n[dark_orange]ALERT from {alert["sender_name"]}[/]')
        print(f'[dark_orange]for[/] [italic dark_orange]{city}, {state}[/]')
        print(f'starts: [#d6d9fe]{rd.datetime_to_dow(start_datetime)}, {start_datestr[11:]}[/]')
        print(f'   end: [#d6d9fe]{rd.datetime_to_dow(end_datetime)}, {end_datestr[11:]}[/]\n')
        print(f'[italic dark_orange]{alert["event"]}[/]')
        print(f'{alert["description"]}\n')


def print_single_day(city, state, latitude, longitude, date, weather, feels_like, humidity, pressure, temperature, max_temp, min_temp, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow) -> None:
    """
    Print the current weather report.

    Example report:

    WEATHER for Tuesday, March 21, 2023, 08:00 AM
    McNair, Virginia: 38.95669, -77.41006
            weather: fog
        temperature: 30.3 °F
            feels like: 30.3 °F
            dew point: 15.7 °F
            humidity: 50%
            pressure: 578.3 mmHg / 22.8 ins
            UV index: 0.0 -- low
            visibility: 6.0 miles
        wind direction: south west
            wind speed: 1.0 mph
                gust: 2.0
            sunrise: 07:11 AM
                sunset: 07:21 PM
    """

    pressure_mmhg: float = convert_pressure(pressure)
    visibility_miles: float = convert_visibility(visibility)

    print(f'\n[dark_orange]WEATHER for {date}[/]', sep="")
    print(f'[italic underline dark_orange]{city}, {state}: {latitude}, {longitude}[/]', sep="")
    print(f'           [dark_orange]weather:[/] [light_steel_blue1]{weather}[/]', sep="")
    print(f'       [dark_orange]temperature:[/] [light_steel_blue1]{temperature:.1f} °F[/]')
    print(f'        [dark_orange]feels like:[/] [light_steel_blue1]{feels_like:.1f} °F[/]')
    print(f'         [dark_orange]dew point:[/] [light_steel_blue1]{dew_point:.1f} °F[/]')
    print(f'          [dark_orange]humidity:[/] [light_steel_blue1]{humidity:.0f}%[/]')
    inhg: float = pressure_mmhg * 0.03937
    print(f'          [dark_orange]pressure:[/] [light_steel_blue1]{pressure_mmhg:.1f} mmHg / {inhg:.1f} ins[/]')
    uvi_color, uv_text = get_uv_index_color(uvi)
    print(f'          [dark_orange]UV index:[/] [{uvi_color}]{uvi} -- {uv_text}[/]')
    print(f'        [dark_orange]visibility:[/] [light_steel_blue1]{visibility_miles:0.1f} miles[/]')
    if snow > 0:
        print(f'              [dark_orange]snow:[/] [light_steel_blue1]{snow:0.1f} in.[/]')
    if rain > 0:
        print(f'              [dark_orange]rain:[/] [light_steel_blue1]{snow:0.1f} in.[/]')
    print(f'    [dark_orange]wind direction:[/] [light_steel_blue1]{wind_direction}[/]')
    print(f'        [dark_orange]wind speed:[/] [light_steel_blue1]{wind_speed:.1f} mph[/]')
    print(f'              [dark_orange]gust:[/] [light_steel_blue1]{gust:.1f}[/]')
    print(f'           [dark_orange]sunrise:[/] [light_steel_blue1]{sunrise}[/]')
    print(f'            [dark_orange]sunset:[/] [light_steel_blue1]{sunset}[/]')


def print_daily_summary(latitude, longitude, city, state, data):
    """
    Print a weather summary for a specific day.

    Example report
    DAILY SUMMARY OF WEATHER for 2024-03-26
    McNair, Virginia: 38.95669, -77.41006
        temperature: 51.3 °F
    min temperature: 36.0 °F
    max temperature: 57.9 °F
        humidity: 51%
    precipitation: 0.00 in.
        pressure: 767.2 mmHg
        cloud cover: 100%
    max wind speed: 11 mph
    wind direction: south east

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    data : dict -- aggregated daily weather for one day
    """

    date = data["date"]
    cloud_cover = data["cloud_cover"]["afternoon"]
    humidity = data["humidity"]["afternoon"]
    precipitation = data["precipitation"]["total"] * 0.03937008
    pressure = convert_pressure(data["pressure"]["afternoon"])
    temperature = data["temperature"]["afternoon"]
    temp_min = data["temperature"]["min"]
    temp_max = data["temperature"]["max"]
    max_wind_speed = data["wind"]["max"]["speed"]
    wind_direction = wind_direction_txt(data["wind"]["max"]["direction"])

    print(f'\n[dark_orange]DAILY SUMMARY OF WEATHER for {date}[/]', sep="")
    print(f'[italic underline dark_orange]{city}, {state}: {latitude}, {longitude}[/]', sep="")
    print(f'[dark_orange]    temperature:[/] [light_steel_blue1]{temperature:.1f} °F[/]')
    print(f'[dark_orange]min temperature:[/] [light_steel_blue1]{temp_min:.1f} °F[/]')
    print(f'[dark_orange]max temperature:[/] [light_steel_blue1]{temp_max:.1f} °F[/]')
    print(f'[dark_orange]       humidity:[/] [light_steel_blue1]{humidity:.0f}%[/]')
    print(f'[dark_orange]  precipitation:[/] [light_steel_blue1]{precipitation:.2f} in.[/]')
    print(f'[dark_orange]       pressure:[/] [light_steel_blue1]{pressure:.1f} mmHg[/]')
    print(f'[dark_orange]    cloud cover:[/] [light_steel_blue1]{cloud_cover:.0f}%[/]')
    print(f'[dark_orange] max wind speed:[/] [light_steel_blue1]{max_wind_speed:.0f} mph[/]')
    print(f'[dark_orange] wind direction:[/] [light_steel_blue1]{wind_direction}[/]')

    # return date, cloud_cover, humidity, precipitation, pressure, temperature, temp_min, temp_max, max_wind_speed, wind_direction


# ==== UTILITY FUNCTIONS =====================================================

def get_location(latitude: float, longitude: float) -> tuple[str, str]:
    """
    For the given latitude and longitude, return the city and state.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest

    Returns
    -------
    tuple[str, str] -- city, state names
    """

    # Use reverse GeoCoding to get city/state given lat and long.
    url = f'http://api.openweathermap.org/geo/1.0/reverse?lat={latitude}&lon={longitude}&limit={5}&appid={API_KEY}'
    r = requests.get(url)
    geo_data = r.json()

    error_msg = f'\n[red1]We encountered an error using "{latitude}" and/or "{longitude}" because, sadly, those coordinates don\'t exist.[/]'

    # If user enters text (e.g., city/state), the CLI will report that a float is required.
    # If user enters city/state that don't exist, a KeyError results.
    try:
        city = geo_data[0]["name"]
        state = geo_data[0]["state"]
    except KeyError:
        print(error_msg)
        exit()

    return city, state


def get_lat_long(city: str, state: str) -> tuple[float, float]:
    """
    For the given city and state, return the latitude and longitude.

    Parameters
    ----------
    city : str -- city of interest
    state : str -- state of interest

    Returns
    -------
    tuple[float, float] -- latitude, longitude
    """

    geo_url: str = f'http://api.openweathermap.org/geo/1.0/direct?q={city},{state}&limit={2}&appid={API_KEY}'
    r = requests.get(geo_url)
    geo_data = r.json()

    error_msg = f'\n[red1]We encountered an error using "{city}" and/or "{state}" due to\n   1. "{city}" and/or "{state}" doesn\'t exist.\n   2. City and state names can\'t be numbers.[/]'

    # If user enters numbers instead of text...
    try:
        state_data = next((item for item in geo_data if item['state'] == state), None)
    except KeyError:
        print(error_msg)
        exit()

    # If user enters a city/state that doesn't exist (in openweathermap's database!)...
    if not state_data:
        print(error_msg)
        exit()

    return state_data['lat'], state_data['lon']


def coord_arguments_ok(lat, lon) -> bool:
    """
    Returns True if the provided latitude and longitude make sense on earth.

    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest

    Returns
    -------
    bool -- True if lat/lon are ok
    """

    if not isinstance(lat, float):
        return False
    if not isinstance(lon, float):
        return False
    if not -90 <= lat <= 90:
        return False
    if not -180 <= lon <= 180:
        return False
    return True


def convert_visibility(visibility: int) -> float:
    """
    Convert visibility from meters to miles.

    Parameters
    ----------
    visibility : int -- visibility reported in json data

    Returns
    -------
    float -- visibility in miles
    """
    return visibility * 0.00062137


def wind_direction_txt(degrees: int) -> str:
    """
    Convert weather direction in degrees to a text representation.

    Parameters
    ----------
    degrees : int -- wind direction in degrees

    Returns
    -------
    str -- text representation of direction: "north", "north east", "east",
                             "south east", "south", "south west", "west", or "north west"
    """

    directions: list[str] = ["north", "north east", "east",
                             "south east", "south", "south west", "west", "north west"]
    index: int = round(degrees / 45) % 8
    return directions[index]


def convert_pressure(p: float) -> float:
    """
    Convert atmospheric pressure in hPa to mmHg.

    Parameters
    ----------
    p : float -- atmospheric pressure in hPa

    Returns
    -------
    float -- mmHg
    """
    return p * 0.750062


def is_single_day_date_ok(timeStamp: float) -> bool:
    """
    single_day data is only available for dates after 01-01-1979 and up to 4 days after the current date. This function determines if the provided date is ok or not.

    Parameters
    ----------
    d : str -- date provided

    Returns
    -------
    bool -- True if the provided date is after 01-01-1979 but before current date + 4 days
    """

    # Convert the string dates to datetime objects
    provided_datestr: str = rd.ts_to_datestr(int(timeStamp))[:10]
    date_format = '%Y-%m-%d'
    provided_date: rd.datetime = rd.datetime.strptime(
        provided_datestr, date_format)
    earliest_date: rd.datetime = rd.datetime.strptime(
        "1979-01-01", date_format)
    latest_date: rd.datetime = rd.datetime.now() + rd.timedelta(days=4)

    # Compare the two datetime objects
    return earliest_date <= provided_date <= latest_date


def get_uv_index_color(uv_index: float) -> tuple[str, str]:
    """
    Get the appropriate color and text for a given UV index.

    1 to 2: Low exposure risk (Green)
    3 to 5: Moderate exposure risk (Yellow)
    6 to 7: High exposure risk (Orange)
    8 to 10: Very high exposure risk (Red)
    11+: Extreme exposure risk (Violet)

    Parameters
    ----------
    uv_index : float -- UV index downloaded in json data

    Returns
    -------
    tuple -- color, text
    """
    if uv_index < 3:
        return "green1", "low"
    elif uv_index <= 5:
        return "green_yellow", "moderate"
    elif uv_index <= 7:
        return "orange3", "high"
    elif uv_index <= 10:
        return "red1", "very high"
    else:
        return "bright_magenta", "extreme"


def get_nearby_stations(latitude, longitude) -> pd.DataFrame:
    """
    Create a dataframe of weather stations nearby a given latitude and longitude. Called by all functions in the "meteostat" group.

    Parameters
    ----------
    latitude : float -- latitude of location
    longitude : float -- longitude of location

    Returns
    -------
    pd.DataFrame -- list of weather stations nearby
    """

    st = Stations()
    stations_nearby: Stations = st.nearby(latitude, longitude)
    stations_df: pd.DataFrame = stations_nearby.fetch(5)
    stations_df['elevation'] = stations_df['elevation'] * 3.2808399
    stations_df['distance'] = stations_df['distance'] * 0.0006213712
    return stations_df


def list_stations(stations_df) -> None:
    """
    Print a list of 5 nearby weather stations, using data from get_nearby_stations(). Called by stations()

    Parameters
    ----------
    stations_df : DataFrame -- list of weather stations
    """

    print()
    for index, row in stations_df.iterrows():
        print(f'{index} {row['name']}: {row['latitude']}, {row['longitude']}, {row['elevation']:0.2f} ft')
        print(f'   distance: {row['distance']:0.2f} miles')
        print(f'     hourly: {row['hourly_start'].strftime('%Y-%m-%d')} - {row['hourly_end'].strftime('%Y-%m-%d')}')
        print(f'      daily: {row['daily_start'].strftime('%Y-%m-%d')} - {row['daily_end'].strftime('%Y-%m-%d')}')
        print(f'    monthly: {row['hourly_start'].strftime('%Y-%m-%d')} - {row['hourly_end'].strftime('%Y-%m-%d')}')
        print()


def save_pandas_data(df: pd.DataFrame) -> None:
    """
    Save pandas dataframe to json. Called by functions under the "meteostat" command.

    Parameters
    ----------
    df : pd.DataFrame -- various dataframes passed in
    """

    user_profile: str = os.environ['USERPROFILE']

    # Define the path to the downloads folder within the user's profile directory
    downloads_folder: str = os.path.join(user_profile, 'Downloads')

    df.to_csv(os.path.join(downloads_folder, 'weather_data.csv'), index=False)


def save_data(data: dict) -> None:
    """
    Save data downloaded from openweathermap.org to a json file.

    Parameters
    ----------
    data : dict -- downloaded data
    """

    user_profile: str = os.environ['USERPROFILE']

    # Define the path to the downloads folder within the user's profile directory
    downloads_folder: str = os.path.join(user_profile, 'Downloads')

    # Convert the Python dictionary to a JSON string
    json_data = json.dumps(data, indent=4)

    data_file = downloads_folder + "\\data.json"
    with open(data_file, 'w', encoding="utf-8") as file:
        # Write the JSON data to the file
        file.write(json_data)


@atexit.register
def last_word() -> None:
    """
    This function is executed no matter how the program exits. It gets a random list of 50 quotes from zenquotes.io each day. From this list, a random quote is selected and printed, and then a "thank you" is printed. By reusing, the list of 50 quotes, "hits" on zenquotes.io is limited to essentially once a day.
    """

    # Get the path to the user's downloads directory.
    user_profile: str = os.environ['USERPROFILE']
    downloads_folder: str = os.path.join(user_profile, 'Downloads')
    quote_file: str = downloads_folder + "\\quotes " + TODAYS_DATE + ".json"

    if os.path.exists(quote_file):
        with open(quote_file, 'r', encoding="utf-8") as file:
            quote_data = json.load(file)
    else:
        print("\nAccessing zenquotes.io...")
        url = "https://zenquotes.io/api/quotes/"

        r = requests.get(url)
        if r.status_code != 200:
            print('\nCould not reach "https://zenquotes.io".', sep="")
            exit()

        quote_data = json.loads(r.text)

        with open(quote_file, 'w', encoding="utf-8") as file:
            json.dump(quote_data, file, indent=4)

    random_quote_number = randint(0, len(quote_data) - 1)

    quote = quote_data[random_quote_number]["q"]
    print(f'\n[steel_blue1]{quote}[/]')

    print("[yellow2]Thanks for using this app. Give somone some love![/]")


if __name__ == "__main__":
    pass
