"""
    Filename: weather.py
     Version: 0.1
      Author: Richard E. Rawson
        Date: 2024-03-08
 Description: Print weather reports to the terminal.

~CUSTOMIZATION:
Customizing defaults requires editing this source code simply be changing DEFAULT values starting at line 47.

RESOURCES:
    https://openweathermap.org/api
    https://openweathermap.org/api/geocoding-api
    https://home.openweathermap.org/statistics/onecall_30 --> for my usage statistics

    https://dev.meteostat.net/python/

-- PROGRAMMING NOTE:
    ! Dates can be entered by user as timezone-unaware dates, but within code, dates are almost always UTC, except where printed to the terminal where the UTC date is converted to the local time zone.
"""


import atexit
import configparser
import json
import os
import warnings
from random import randint

import click
import pandas as pd
import rdatetime as rd
import requests
from icecream import ic
from meteostat import Daily, Hourly, Monthly, Normals, Point, Stations
from rich import print

warnings.filterwarnings('ignore', category=FutureWarning)

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY: str = config['DEFAULT']['API_KEY']


VERSION = "0.1"

DEFAULT_LAT: str = "38.95669"
DEFAULT_LON: str = "-77.41006"
DEFAULT_CITY: str = "Herndon"
DEFAULT_STATE: str = "Virginia"

# Create a naive date string for today's date in YYYY-MM-DD format.
todaydatetime: rd.datetime = rd.datetime.now()
todaynaive: rd.datetime = rd.tzdatetime_to_naivedatetime(todaydatetime)
TODAYS_DATE: str = rd.datetime_to_datestr(todaynaive, fmt="%Y-%m-%d")


# CODENOTE Using "invoke_without_command=True" allows cli() to execute if weather.py is run with no arguments. If false, then running weather.py without arguments is the same as weather.py --help.

@click.group(invoke_without_command=True, epilog=f'Except \"meteostat\", using commands without arguments retrieves weather data for \"today\" at lat/lon =[{DEFAULT_LAT}, {DEFAULT_LON}] or city/state = [{DEFAULT_CITY}, {DEFAULT_STATE}]. These commands aim to provide weather information for the immediate time period. \n\n\"meteostat\" exposes 6 subcommands for accessing ranges of weather data in bulk, from a single day/time to one-day-a-month over 30 years. Bulk data are saved to file for analysis by other programs.')
@click.version_option(version=VERSION)
@click.pass_context
def cli(ctx) -> None:
    """
    Display weather reports or alerts for location (city/state) or coords (latitude/longitude). This weather app is replete with defaults. Executing the app with no arguments is the same as:

    coords -p forecast -lat (default lat) -lon (default lon)

    \b
    Further, every command has similar defaults, as needed.
    See <command> --help for each command for details.
    Example: python weather.py location --help

    Commands organized by period:

    \b
    Today's current or forecasted weather
        location        Current or forecasted weather
        coords          Current or forecasted weather
        alerts          Currently issued weather alerts

    \b
    Detailed weather
        hourly-forecast Hourly forecast for up to 48 hours
        rain-forecast   Rain for next hour

    \b
    Weather summaries
        daily-summary   Mean or total values on the provided [DATE]
        meteostat
            single-day  Data for a specific day and time
            daily       Data in daily increments
            hourly      Data  in hourly increments
            monthly     Data  in monthly increments
            summary     summary statistics for variables between two dates
            normals     Normal weather data for 30-year period
            stations    Five meteorological stations nearest to a location

    \b
    manual              Access this user manual
    \f
    Parameters
    ----------
    ctx : dict -- current context
    period : str -- one of: current weather or forecast weather
    """

    # If there are no arguments on the command line, then the "if" code will run,
    # resulting in a default weather report that will be the same as using:
    # coords -p current -lat DEFAULT_LAT -lon DEFAULT_LON
    if ctx.invoked_subcommand is None:
        # else:
        latitude: float = float(DEFAULT_LAT)
        longitude: float = float(DEFAULT_LON)
        city, state = get_location(latitude, longitude)

        get_weather_report('forecast', latitude, longitude, city, state, days=2)


@click.command(epilog='Use the --period option to deliver either current or forecasted weather.\n\nIf an alert has been issued, that information is displayed without having to issue the "alerts" command.')
@click.option("-p", "--period", type=click.Choice(['current', 'forecast']), default='forecast', show_default=True, help="The time period for the report.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather report for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.option('-d', '--days', type=int, default=2, show_default=True)
@click.pass_context
def location(ctx, period, city, state, days) -> None:
    """
Current or forecasted weather. This command takes city/state as arguments, not lat/lon.

EXAMPLE USAGE:

\b
    location --> forecast weather for default location

    location -p forecast --city Ithaca --state "New York" --> 8-day forecast for Ithaca

EXAMPLE DATA: location -p forecast -c Alexandria -s Virginia

\b
    FORECAST for Alexandria, Virginia
    Today: Tuesday, March 26:
    There will be partly cloudy today.
        Temperature low: 38 °F
    Temperature high: 57 °F
            Humidity: 57%
            Wind speed: 9 mph
        Chance of rain: 0%
    Expected rain fall: 0.00 in.
    Wednesday:
    Expect a day of partly cloudy with rain.
        Temperature low: 43 °F
    ...
    \f
    Parameters
    ----------
    ctx : dict -- current context
    city : str -- city of interest
    state : str -- state of interest
    """

    latitude, longitude = get_lat_long(city, state)

    get_weather_report(period, latitude, longitude, city, state, days)

    return None


@click.command(epilog='Use --period option to deliver either current or forecasted weather.\n\nIf an alert has been issued, that information is displayed without having to issue the "alerts" command.')
@click.option("-p", "--period", type=click.Choice(['current', 'forecast']), default='forecast', show_default=True, help="The time period for the report.")
@click.option('-lat', "--latitude", type=float, default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default=DEFAULT_LON, show_default=True, help="Longitude for location.")
@click.option('-d', '--days', type=int, default=2, show_default=True)
@click.pass_context
def coords(ctx, period, latitude, longitude, days) -> None:
    """
Current or forecasted weather. This command latitude/longitude as arguments, not city/state.

EXAMPLE USAGE:

\b
    coords --> forecast weather for default latitude and longitude

    coords -p forecast -lat 42.4372 -lon -76.5484 --> 8-day forecast for this latitude/longitude

EXAMPLE DATA: coords -p current -lat 38.9695316 -lon -77.3859479

\b
    CURRENT WEATHER for
    Tuesday, March 26, 2024, 11:07 AM
    Herndon, Virginia: 38.9695316, -77.3859479
            weather: broken clouds
        temperature: 47.5 °F
            feels like: 46.8 °F
            dew point: 31.7 °F
            humidity: 54%
            pressure: 575.5 mmHg / 22.7 ins
            UV index: 1.6 -- low
            visibility: 6.2 miles
        wind direction: north
            wind speed: 3.0 mph
                gust: 3.0
            sunrise: 07:02 AM
                sunset: 07:27 PM

    \f
    Parameters
    ----------
    ctx : dict -- current context
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    """

    city, state = get_location(latitude, longitude)

    get_weather_report(period, latitude, longitude, city, state, days)

    return None


@click.command(epilog="--hours option can limit the number of hours reported. This report includes time, temperature, UVI, weather description, and chance of rain.")
@click.option('-lat', "--latitude", type=float, default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default=DEFAULT_LON, show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.option('-h', '--hours', default=8, show_default=True, help="Number of hours to report")
@click.pass_context
def hourly_forecast(ctx, latitude, longitude, city, state, hours) -> None:
    """
Forecast for the provided location, hourly.

EXAMPLE USAGE:

\b
    hourly-forecast -> next 8 hours forecast for default location

    hourly-forecast --latitude (default lat) --longitude (default lon) --hours 8

EXAMPLE DATA: hourly-forecast -h 2

\b
Hourly forecast for McNair, Virginia
Tuesday, Mar 26, 2024
           11:00 AM                      12:00 PM
        broken clouds                 broken clouds
     Temperature: 48 °F            Temperature: 48 °F
            rain: 0.00 in.                rain: 0.00 in.
             UVI: 1.6                      UVI: 2.82
  Chance of rain: 0 %           Chance of rain: 0 %
    """

    # If user entered city/state, convert to latitude/longitude first.
    if city != DEFAULT_CITY and state != DEFAULT_STATE:
        latitude, longitude = get_lat_long(city, state)

    if coord_arguments_ok(latitude, longitude):
        data = get_hourly_forecast_data(latitude, longitude)

        print_hourly_forecast(latitude, longitude, data, hours)

    else:
        error_msg = f'\nWe encountered an error with latitude={latitude} or longitude={longitude}. Either:\n   1. Latitude and/or longitude were entered as non-numbers.\n   2. Latitude and/or longitude were not in the ranges of -90 to 90 or -180 to 180, respectively.'
        print(f'[red1]{error_msg}[/]', sep="")


@click.command(epilog="Rain forecast is reported at 5 minute intervals for the next hour.")
@click.option('-lat', "--latitude", type=float, default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default=DEFAULT_LON, show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.pass_context
def rain_forecast(ctx, latitude, longitude, city, state) -> None:
    """
Rain for next hour in 5-min intervals.

EXAMPLE USAGE:

    \b
    rain-forecast --> forecast for default location for the next hour
    rain_forecast --latitude (default lat) --longitude (default lon)

EXAMPLE DATA: rain-forecast (no arguments)

    \b
    Expected rainfall in the next hour
    2024-03-26 -- McNair, Virginia
    11:14: 0.00 in.
    11:19: 0.00 in.
    11:24: 0.00 in.
    11:29: 0.00 in.
    """

    # If user entered city/state, convert to latitude/longitude first.
    if city != DEFAULT_CITY and state != DEFAULT_STATE:
        latitude, longitude = get_lat_long(city, state)

    if coord_arguments_ok(latitude, longitude):
        print("\n[dark_orange]Expected rainfall in the next hour[/]")
        data = get_rain_forecast_data(latitude, longitude)

        print_rain_forecast(latitude, longitude, data)

    else:
        error_msg = f'\nWe encountered an error with latitude={latitude} or longitude={longitude}. Either:\n   1. Latitude and/or longitude were entered as non-numbers.\n   2. Latitude and/or longitude were not in the ranges of -90 to 90 or -180 to 180, respectively.'
        print(f'[red1]{error_msg}[/]', sep="")


@click.command(epilog="If there is an alert, that information is included automatically in the current weather report (location or coords commands).")
@click.option('-lat', "--latitude", type=float, default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default=DEFAULT_LON, show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.pass_context
def alerts(ctx, latitude, longitude, city, state) -> None:
    """
Currently issued weather alerts.

EXAMPLE USAGE:

\b
    alerts --> current alerts for the default location

EXAMPLE DATA: alerts (no arguments)

\b
    ALERT from NWS Baltimore MD/Washington DC
    for McNair, Virginia
    starts: Tuesday, 07:00 PM
    end: Wednesday, 03:00 PM

    Coastal Flood Advisory
    * WHAT...Up to one half foot of inundation above ground level expected in low lying areas due to tidal flooding.

    * WHERE...Fairfax, Stafford and Southeast Prince William Counties.
    ...
    """

    # If user entered city/state, convert to latitude/longitude first.
    if city != DEFAULT_CITY and state != DEFAULT_STATE:
        latitude, longitude = get_lat_long(city, state)

    if coord_arguments_ok(latitude, longitude):

        city, state = get_location(latitude, longitude)

        # "filter_times" are the periods to filter OUT.
        filter_times: str = "current,minutely,hourly,daily"
        data = download_data(latitude, longitude, filter_times)

        # Check to see if there actually is an alert:
        try:
            sender = data['alerts'][0]["sender_name"]
        except KeyError:
            print(f'\n[dark_orange]No alerts have been issued for[/] [#d6d9fe]{city}, {state}[/]', sep="")
            return None

        print_alerts(city, state, data)

    else:
        error_msg = f'\nWe encountered an error with latitude={latitude} or longitude={longitude}. Either:\n   1. Latitude and/or longitude were entered as non-numbers.\n   2. Latitude and/or longitude were not in the ranges of -90 to 90 or -180 to 180, respectively.'
        print(f'[red1]{error_msg}[/]', sep="")


@click.command(epilog="A daily summary provides summary data for a day's worth of weather information. For example, temperature would represent the average temperature for the day and precipitation reports to total rainfall for the day.")
@click.option('-lat', "--latitude", type=float, default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default=DEFAULT_LON, show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
# @click.option('-d', '--date', default=default_date, show_default=False, help="Date for weather report.  [default: today]")
@click.argument("date", required=True, default=TODAYS_DATE)
@click.pass_context
def daily_summary(ctx, latitude, longitude, city, state, date) -> None:
    """
Report mean or total values for the provided [DATE]. The default [DATE] is today.

EXAMPLE USAGE:

    daily-summary -c Herndon -s Virginia 2023-03-20



EXAMPLE DATA: daily-summary 2023-03-20

\b
    DAILY SUMMARY OF WEATHER for 2023-03-20
    McNair, Virginia: 38.95669, -77.41006
        temperature: 28.1 °F
    min temperature: 25.4 °F
    max temperature: 50.5 °F
        humidity: 52%
    precipitation: 0.00 in.
        pressure: 769.6 mmHg
        cloud cover: 0%
    max wind speed: 24 mph
    wind direction: west
    \f
    Parameters
    ----------
    ctx : context -- _description_
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    date : str -- naive date for which report is requested

    """

    # If user entered city/state, convert to latitude/longitude first.
    if city != DEFAULT_CITY and state != DEFAULT_STATE:
        latitude, longitude = get_lat_long(city, state)

    # Convert the provided date to YYYY-MM-DD format and eliminate any time entered,
    # since the aggregate data is for the whole day, not a specific time
    datetimeobj: rd.datetime = rd.datestr_to_tzdatetime(date)
    datestr: str = rd.datetime_to_datestr(datetimeobj)
    date: str = datestr[:10]

    url: str = f'https://api.openweathermap.org/data/3.0/onecall/day_summary?lat={latitude}&lon={longitude}&units=imperial&date={date}&appid={API_KEY}'
    r = requests.get(url)
    if r.status_code != 200:
        print('\nCould not reach "https://api.openweathermap.org".', sep="")
        exit()

    data = r.json()
    save_data(data)

    city, state = get_location(latitude, longitude)

    print_daily_summary(latitude, longitude, city, state, data)

    return None


# ==== meteostat GROUP OF COMMANDS ===========================================

"""
From here up to the next section, all functions relate to the "meteostat" command and include:

single_day
daily
hourly
monthly
normals
stations
summary
"""


@click.group(invoke_without_command=True, epilog="Data are based on the weather station closest to the provided latitude/longitude. Use \"meteostat stations\" to list the five closest stations.")
@click.version_option(version=VERSION)
@click.pass_context
def meteostat(ctx) -> None:
    """
Report bulk meteorological data for a variety of periods. Latitude and longitude default to Dulles International Airport. Data are saved in \"USERPROFILE\\downloads\\weather_data.csv\" after each report is run.

    \b
  single-day: Data for a specific day and time (default time: 12:00pm)
       daily: Data are reported in daily increments.
      hourly: Data are reported in hourly increments.
     monthly: Data are reported in monthly increments.
     summary: count, mean, std dev, min, and max values for weather variable between provided dates.
     normals: Normal weather data for 30-year period reported as average values for each of 12 months.
    stations: List five meteorological stations nearest to the provided latitude/longitude.
    \f
    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    startdate : str -- start date for weather data
    enddate : str -- end date for weather data
    period : str -- period of report: hourly, daily, monthly, summary, normals, stations
    """
    if ctx.invoked_subcommand is None:
        print("\nmeteostat cannot be used independent of subcommands.\n\nUSAGE: meteostat [OPTIONS] COMMAND [ARGS]...\nEXAMPLE USAGE:\n     meteostat summary\n     meteostat summary -lat 38.93485 -lon -77.44728\n\nSee --help for more information.")


@click.command(epilog="Default date/time is today at 12:00 pm. Date/time can be entered in various formats, but a standard format is YYYY-MM-DD H:M. \"H:M\" can be either \"2:00 pm\" or \"14:00\".")
@click.option('-lat', "--latitude", type=float, default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default=DEFAULT_LON, show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City of interest.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="City's state.")
# @click.option('-d', '--date', default=default_date, show_default=False, help="Date for weather report.  [default: today]")
@click.argument("date", required=True, default=TODAYS_DATE)
@click.pass_context
def single_day(ctx, latitude, longitude, city, state, date) -> None:
    """
Report weather for the provided [DATE]. [DATE] must be on or after Jan 1, 1979 and up to 4 days from today's date. See epilog for formatting [DATE].

Example data: meteostat single-day 2023-03-01

\b
    WEATHER for Wednesday, March 01, 2023, 07:00 AM
    McNair, Virginia: 38.95669, -77.41006
            weather: few clouds
        temperature: 33.7 °F
            feels like: 33.7 °F
            dew point: 28.4 °F
            humidity: 79%
            pressure: 573.8 mmHg / 22.6 ins
            UV index: 0.0 -- low
            visibility: 6.2 miles
        wind direction: north
            wind speed: 0.0 mph
                gust: 0.0
            sunrise: 06:42 AM
                sunset: 06:01 PM
    \f
    Parameters
    ----------
    ctx : _type_ -- _description_
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    date : str -- naive date/time for which report is requested

    CODENOTE: This function is the only one in the "meteostat" group that gets data from openweathermap.org. All other commands get data from meteostat.net.
    """

    # If user entered city/state, convert to latitude/longitude first.
    if city != DEFAULT_CITY and state != DEFAULT_STATE:
        latitude, longitude = get_lat_long(city, state)

    if len(date) == 10:
        date += " 12:00"

    localdatetime: rd.datetime = rd.datestr_to_tzdatetime(date)
    UTCts: int = int(rd.datetime_to_ts(localdatetime))

    # Make sure provided date is after 01-01-1979.
    if not is_single_day_date_ok(UTCts):
        print(f'\nProvided date \"{date}\" must be on or after \"01-01-1979\" but no later than 4 days from today.', sep="")
        exit()

    # Find the corresponding city/state for the provide lat/lon.
    city, state = get_location(latitude, longitude)

    # Retrieve the data from openweathermap.org for the provided date.
    data = get_single_day_data(latitude, longitude, UTCts)

    # From the downloaded data, get the variables we want.
    date, weather, feels_like, humidity, pressure, temperature, max_temp, min_temp, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow = extract_single_day_weather_vars(
        data)

    # Print the final report.
    print_single_day(city, state, latitude, longitude, date, weather, feels_like, humidity, pressure, temperature, max_temp, min_temp, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow, alerts)

    return None


# Default lat and lon is for Dulles International Airport, the closest
# meteorological station to McNair, VA
@click.command(epilog="Example usage:\nmeteostat daily 2023-03-01 2023-03-03")
@click.option('-lat', "--latitude", type=float, default="38.93485", show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default="-77.44728", show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.argument("startdate", required=True, default="1960-01-01")
@click.argument("enddate", required=True, default=TODAYS_DATE)
@click.pass_context
def daily(ctx, latitude, longitude, city, state, startdate, enddate) -> None:
    """
Report means or totals for each day between two dates. Default dates: 1960-01-01 to today.

\b
EXAMPLE DATA: meteostat daily 2023-03-01 2023-03-03

\b
            Avg temp  Min temp  Max temp  Rain  Snow  Wind Dir  Wind Spd  Pressure
time
2023-03-01      44.2      27.9      59.7  0.00   0.0     163.0       7.0     761.9
2023-03-02      52.7      40.6      63.7  0.01   0.0     328.0       7.0     755.5
2023-03-03      41.9      36.7      45.7  0.56   0.0      62.0       7.0     758.1
...
    \f
    Parameters
    ----------
    ctx : _type_ -- _description_
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    startdate : str -- starting date
    enddate : str -- ending date

    """

    # Get the first weather station nearby the provided latitude/longitude.
    # Use that station's latitude, longitude, and elevation to instantiate a "Point" that
    # corresponds to the weather station's location.
    stations_df: pd.DataFrame = get_nearby_stations(latitude, longitude)
    dulles = Point(stations_df.iloc[0, 5], stations_df.iloc[0, 6], stations_df.iloc[0, 7])

    weather_station = stations_df.iloc[0, 0]

    city, state = get_location(latitude, longitude)

    startdatetime: rd.datetime = rd.datestr_to_tzdatetime(startdate)
    start: rd.datetime = rd.tzdatetime_to_naivedatetime(startdatetime)
    enddatetime: rd.datetime = rd.datestr_to_tzdatetime(enddate)
    end: rd.datetime = rd.tzdatetime_to_naivedatetime(enddatetime)

    # Get daily data for period
    # daily_data = Daily(stations_df.index[0])
    daily_data = Daily(dulles, start, end)
    ddata: pd.DataFrame = daily_data.fetch()

    # Save the raw downloaded data.
    save_pandas_data(ddata)

    # Convert some date from metric to imperial. lambda functions avoid errors with NaN.
    ddata['tavg'] = ddata['tavg'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    ddata['tmin'] = ddata['tmin'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    ddata['tmax'] = ddata['tmax'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    ddata['prcp'] = ddata['prcp'].apply(lambda x: round(x * 0.03937008, 2) if pd.notnull(x) else x)
    ddata['snow'] = ddata['snow'].apply(lambda x: round(x * 0.03937008, 2) if pd.notnull(x) else x)
    ddata['wspd'] = ddata['wspd'].apply(lambda x: round(x * 0.62137119, 0) if pd.notnull(x) else x)
    ddata['wdir'] = ddata['wdir'].apply(lambda x: round(x * 1, 0) if pd.notnull(x) else x)
    ddata['pres'] = ddata['pres'].apply(lambda x: round(x * 0.750062, 1) if pd.notnull(x) else x)

    # Rename columns.
    ddata.columns = ["Avg temp", "Min temp", "Max temp", "Rain", "Snow", "Wind Dir", "Wind Spd", "Wind gust", "Pressure", "tsun"]

    print(f'\n[dark_orange]{city}, {state}\nStation: {weather_station}\nWeather data for {startdate} to {enddate}[/]\n', sep="")
    print(f'       Mean temp: {ddata.loc[:, "Avg temp"].mean():0.1f} °F', sep="")
    print(f'Highest max temp: {ddata.loc[:, "Min temp"].max():0.1f} °F', sep="")
    print(f' Lowest min temp: {ddata.loc[:, "Max temp"].min():0.1f} °F', sep="")
    print(f'   Mean Wind Spd: {ddata.loc[:, "Wind Spd"].mean():0.0f} mph', sep="")
    print(f'    Max Wind Spd: {ddata.loc[:, "Wind Spd"].max():0.0f} mph', sep="")
    print(f'    Min Wind Spd: {ddata.loc[:, "Wind Spd"].min():0.0f} mph', sep="")

    print(f'  Total rainfall: {ddata.loc[:, "Rain"].sum():0.2f} in.', sep="")
    print(f'  Total snowfall: {ddata.loc[:, "Snow"].sum():0.2f} in.', sep="")
    print()

    print(ddata.loc[:, ["Avg temp", "Min temp", "Max temp", "Rain", "Snow", "Wind Dir", "Wind Spd", "Pressure"]])

    return None


# Default lat and lon is for Dulles International Airport, the closest
# meteorological station to McNair, VA
@click.command(epilog="CAUTION: Using default dates is not recommended. Accessing the 438,000 hours associate with using these dates takes a considerable amount of time.")
@click.option('-lat', "--latitude", type=float, default="38.93485", show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default="-77.44728", show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.argument("startdate", required=True, default="1973-01-01")
@click.argument("enddate", required=True, default=TODAYS_DATE)
@click.pass_context
def hourly(ctx, latitude, longitude, city, state, startdate, enddate) -> None:
    """
Get weather data every hour between two dates/times. Default dates: 1973-01-01 to today. See CAUTION below.

\b
EXAMPLE DATA: meteostat hourly 2023-03-01 2023-03-03

\b
                     Temp  Dew Point  Humidity  Rain  Snow  Wind Dir  Wind Spd  Pressure
time
2023-03-01 00:00:00  50.0       35.8      58.0  0.00   NaN     340.0       6.0     761.4
2023-03-01 01:00:00  48.9       35.2      59.0  0.00   NaN      30.0       7.0     762.0
2023-03-01 02:00:00  48.9       35.2      59.0  0.00   NaN      30.0       7.0     762.0
...
2023-03-02 21:00:00  63.0       38.8      41.0  0.00   NaN     320.0      14.0     754.9
2023-03-02 22:00:00  61.0       35.2      38.0  0.00   NaN     330.0      14.0     756.1
2023-03-02 23:00:00  59.0       32.0      36.0  0.00   NaN     330.0      13.0     756.8
2023-03-03 00:00:00  57.0       30.4      36.0  0.00   NaN     330.0       8.0     757.6
...
    \f
    Parameters
    ----------
    ctx : _type_ -- _description_
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    startdate : str -- starting date
    enddate : str -- ending date

    """

    start = rd.datestr_to_tzdatetime(startdate)
    start = start.replace(tzinfo=None)
    end = rd.datestr_to_tzdatetime(enddate)
    end = end.replace(tzinfo=None)

    # diff: rd.timedelta = end - start
    # if diff.days > 2:
    #     print("Please choose a date range of less than 3 days.")
    #     exit()

    stations_df: pd.DataFrame = get_nearby_stations(latitude, longitude)

    # Get the name of the weather station.
    weather_station = stations_df.iloc[0, 0]

    city, state = get_location(stations_df.iloc[0, 5], stations_df.iloc[0, 6])

    # Get the first weather station nearby the provided latitude/longitude.
    # Use that station's latitude, longitude, and elevation to instantiate a "Point" that
    # corresponds to the weather station's location.

    hourly_data = Hourly(stations_df.index[0], start, end)
    hdata: pd.DataFrame = hourly_data.fetch()

    # Save the raw downloaded data.
    save_pandas_data(hdata)

    # Comvert some date from metric to imperial.
    hdata['temp'] = hdata['temp'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    hdata['dwpt'] = hdata['dwpt'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    hdata['prcp'] = hdata['prcp'].apply(lambda x: round(x * 0.03937008, 2) if pd.notnull(x) else x)
    hdata['snow'] = hdata['snow'].apply(lambda x: round(x * 0.03937008, 2) if pd.notnull(x) else x)
    hdata['wdir'] = hdata['wdir'].apply(lambda x: round(x * 1, 0) if pd.notnull(x) else x)
    hdata['wspd'] = hdata['wspd'].apply(lambda x: round(x * 0.62137119, 0) if pd.notnull(x) else x)
    hdata['pres'] = hdata['pres'].apply(lambda x: round(x * 0.750062, 1) if pd.notnull(x) else x)

    # Rename columns.
    hdata.columns = ["Temp", "Dew Point", "Humidity", "Rain", "Snow", "Wind Dir", "Wind Spd", "Wind gust", "Pressure", "tsun", "coco"]

    # Print the downloaded data.
    print(f'\n[dark_orange]{city}, {state}\nStation: {weather_station}\nWeather data for {startdate} to {enddate}\nLatitude: {stations_df.iloc[0, 5]}, Longitude: {stations_df.iloc[0, 6]}[/]\n', sep="")
    print(f'     Mean Temp: {hdata.loc[:, "Temp"].mean():0.1f} °F', sep="")
    print(f'      Max Temp: {hdata.loc[:, "Temp"].max():0.1f} °F', sep="")
    print(f'      Min Temp: {hdata.loc[:, "Temp"].min():0.1f} °F', sep="")
    print(f'Mean Dew Point: {hdata.loc[:, "Dew Point"].mean():0.1f} °F', sep="")
    print(f' Mean Humidity: {hdata.loc[:, "Humidity"].mean().round().astype(int)}%', sep="")
    print(f' Mean Wind Spd: {hdata.loc[:, "Wind Spd"].mean().round().astype(int)}', sep="")
    print(f'  Max Wind Spd: {hdata.loc[:, "Wind Spd"].max().round().astype(int)}', sep="")
    print(f'  Min Wind Spd: {hdata.loc[:, "Wind Spd"].min().round().astype(int)}', sep="")

    print(f'Total rainfall: {hdata.loc[:, "Rain"].sum():0.2f} in.', sep="")
    print(f'Total snowfall: {hdata.loc[:, "Snow"].sum():0.2f} in.', sep="")
    print()

    data: pd.DataFrame = hdata.loc[:, ["Temp", "Dew Point", "Humidity", "Rain", "Snow", "Wind Dir", "Wind Spd", "Pressure"]]

    print(data)

    hourly_info: dict[str, str] = {"station": "The Meteostat ID of the weather station (only if query refers to multiple stations)",
                                   "time": "The datetime of the observation",
                                   "temp": "The air temperature in °C",
                                   "dwpt": "The dew point in °C",
                                   "rhum": "The relative humidity in percent (%)",
                                   "prcp": "The one hour precipitation total in mm",
                                   "snow": "The snow depth in mm",
                                   "wdir": "The average wind direction in degrees (°)",
                                   "wspd": "The average wind speed in km/h",
                                   "wpgt": "The peak wind gust in km/h",
                                   "pres": "The average sea-level air pressure in hPa",
                                   "tsun": "The one hour sunshine total in minutes (m)",
                                   "coco": "The weather condition code"}

    return None


@click.command()
# Default lat and lon is for Dulles International Airport, the closest
# meteorological station to McNair, VA
@click.option('-lat', "--latitude", type=float, default="38.93485", show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default="-77.44728", show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.argument("startdate", required=True, default="1960-01-01")
@click.argument("enddate", required=True, default=TODAYS_DATE)
@click.pass_context
def monthly(ctx, latitude, longitude, city, state, startdate, enddate) -> None:
    """
Report first-of-the-month weather data between two dates. Default dates: 1960-01-01 to today

\b
EXAMPLE DATA: meteostat monthly 2023-03-01 2023-06-01

\b
Fairfax County, Virginia
Station: Dulles International Airport
Weather data for 2023-03-01 to 2023-06-01
Latitude: 38.9333, Longitude: -77.45

\b
            Mean Temp: 57.98 °F
     Highest max Temp: 55.90 °F
      Lowest min Temp: 55.00 °F
        Mean Wind Spd: 8
         Max Wind Spd: 9
         Min Wind Spd: 6
        Mean pressure: 761.10 in.
Mean monthly rainfall: 2.16 in.
       Total rainfall: 8.65 in.

\b
            Avg Temp  Min Temp  Max Temp  Precipitation  Wind spd  Pressure
time
2023-03-01      44.2      33.3      55.0           1.57       9.0       NaN
2023-04-01      58.1      43.3      70.3           3.30       8.0     762.1
2023-05-01      60.3      47.3      72.3           1.48       6.0     762.8
2023-06-01      69.3      55.9      80.6           2.30       7.0     758.4
    \f
    Parameters
    ----------
    ctx : _type_ -- _description_
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    startdate : str -- starting date
    enddate : str -- ending date
    """

    # Get the first weather station nearby the provided latitude/longitude.
    # Use that station's latitude, longitude, and elevation to instantiate a "Point" that
    # corresponds to the weather station's location.
    stations_df: pd.DataFrame = get_nearby_stations(latitude, longitude)
    dulles = Point(stations_df.iloc[0, 5], stations_df.iloc[0, 6], stations_df.iloc[0, 7])

    # Get the first weather station in stations_df. This is the closest station to lat/lon.
    weather_station = stations_df.iloc[0, 0]

    city, state = get_location(stations_df.iloc[0, 5], stations_df.iloc[0, 6])

    startdatetime: rd.datetime = rd.datestr_to_tzdatetime(startdate)
    start = rd.tzdatetime_to_naivedatetime(startdatetime)
    enddatetime: rd.datetime = rd.datestr_to_tzdatetime(enddate)
    end = rd.tzdatetime_to_naivedatetime(enddatetime)

    # Download monthly data.
    monthly = Monthly(dulles, start, end)
    mdata: pd.DataFrame = monthly.fetch()

    # Save the DataFrame to a CSV file in the USERPROFILE/Documents directory.
    save_pandas_data(mdata)

    # Comvert some date from metric to imperial.
    mdata['tavg'] = mdata['tavg'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    mdata['tmin'] = mdata['tmin'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    mdata['tmax'] = mdata['tmax'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    mdata['prcp'] = mdata['prcp'].apply(lambda x: round(x * 0.03937008, 2) if pd.notnull(x) else x)
    mdata['wspd'] = mdata['wspd'].apply(lambda x: round(x * 0.62137119, 0) if pd.notnull(x) else x)
    mdata['pres'] = mdata['pres'].apply(lambda x: round(x * 0.750062, 1) if pd.notnull(x) else x)

    mdata.columns = ["Avg Temp", "Min Temp", "Max Temp", "Precipitation", "Wind spd", "Pressure", "Total Sun"]

    # # Print the downloaded data.
    print(f'\n{city}, {state}\nStation: {weather_station}\nWeather data for {startdate} to {enddate}\nLatitude: {stations_df.iloc[0, 5]}, Longitude: {stations_df.iloc[0, 6]}\n', sep="")

    print(f'            Mean Temp: {mdata.loc[:, "Avg Temp"].mean():0.2f} °F', sep="")
    print(f'     Highest max Temp: {mdata.loc[:, "Min Temp"].max():0.2f} °F', sep="")
    print(f'      Lowest min Temp: {mdata.loc[:, "Max Temp"].min():0.2f} °F', sep="")
    print(f'        Mean Wind Spd: {mdata.loc[:, "Wind spd"].mean().round().astype(int)} mph', sep="")
    print(f'         Max Wind Spd: {mdata.loc[:, "Wind spd"].max().round().astype(int)} mph', sep="")
    print(f'         Min Wind Spd: {mdata.loc[:, "Wind spd"].min().round().astype(int)} mph', sep="")
    print(f'        Mean pressure: {mdata.loc[:, "Pressure"].mean():0.2f} in.', sep="")

    print(f'Mean monthly rainfall: {mdata.loc[:, "Precipitation"].mean():0.2f} in.', sep="")
    print(f'       Total rainfall: {mdata.loc[:, "Precipitation"].sum():0.2f} in.', sep="")
    print()

    print(mdata.loc[:, ['Avg Temp', 'Min Temp', 'Max Temp', 'Precipitation', 'Wind spd', 'Pressure']])


# Default lat and lon is for Dulles International Airport, the closest
# meteorological station to McNair, VA
@click.command(epilog="Example usage:\nmeteostat normals\n\nWhile it is possible to enter start and end dates, it is recommended to leave the default dates in place.")
@click.option('-lat', "--latitude", type=float, default="38.93485", show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default="-77.44728", show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.argument("startdate", required=True, default="1991-01-01")
@click.argument("enddate", required=True, default="2020-01-01")
@click.pass_context
def normals(ctx, latitude, longitude, city, state, startdate, enddate) -> None:
    """
Normals at a given location calculated over 30 years. Default is 1991 to 2020.

\b
Example data:
       Avg Temp  Min temp  Max temp  Precip  Wind Spd  Pressure  Total Sun
month
1          -0.2      -5.2       4.7    74.5      12.6    1019.8        NaN
2           1.2      -4.3       6.6    64.3      13.0    1018.4        NaN
3           5.5      -0.5      11.5    89.0      13.8    1017.2        NaN

\b
Criteria for the date range:
        1. Both start and end year are required.
        2. end - start must equal 29.
        3. end must be an even decade (e.g., 1990, 2020)
        4. end must be earlier than the current year
    \f
    Parameters
    ----------
    ctx : _type_ -- _description_
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    """

    # Get the first weather station nearby the provided latitude/longitude.
    # Use that station's latitude, longitude, and elevation to instantiate a "Point" that
    # corresponds to the weather station's location.
    stations_df: pd.DataFrame = get_nearby_stations(latitude, longitude)
    dulles = Point(stations_df.iloc[0, 5], stations_df.iloc[0, 6], stations_df.iloc[0, 7])

    # Get normal values from 1991 to 2020.
    normals = Normals(dulles, 1991, 2020)
    ndata: pd.DataFrame = normals.fetch()

    # Save the DataFrame to a CSV file in the USERPROFILE/Documents directory.
    save_pandas_data(ndata)

    # Print normal data as means.
    print('\n[dark_orange]NORMALS CALCULATED MONTHLY FROM 1991 TO 2020[/]\n')

    print('[dark_orange]Annual values:[/]')
    print(f'  Temperature: {round(ndata.loc[0:, 'tavg'].mean(), 1)}')
    print(f'     Min Temp: {round(ndata.loc[0:, 'tmin'].mean(), 1)}')
    print(f'     Max Temp: {round(ndata.loc[0:, 'tmax'].mean(), 1)}')
    print(f'   Wind speed: {round(ndata.loc[0:, 'wspd'].mean(), 1)}')
    print(f'     Pressure: {round(ndata.loc[0:, 'pres'].mean(), 1)}')
    print(f'    Total sun: {round(ndata.loc[0:, 'tsun'].mean(), 1)}')
    print(f'  Mean precip: {round(ndata.loc[0:, 'prcp'].mean(), 1)}')
    print(f' Total precip: {round(ndata.loc[0:, 'prcp'].sum(), 1)}')
    print()

    ndata.columns = ["Avg Temp", "Min temp", "Max temp", "Precip", "Wind Spd", "Pressure", "Total Sun"]
    print(ndata)


@click.command(epilog="Example usage:\nmeteostat stations -lat 38.95669 -lon -77.41006")
# Default lat and lon is for Dulles International Airport, the closest
# meteorological station to McNair, VA
@click.option('-lat', "--latitude", type=float, default="38.93485", show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default="-77.44728", show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.pass_context
def stations(ctx, latitude, longitude, city, state) -> None:
    """
List stations nearby to the provided latitude and longitude. City/state, if used, are converted to lat/lon, which are then used for data gathering.

\b
Example data: meteostat stations -lat 38.9695316 -lon -77.3859479
72403 Dulles International Airport: 38.9333, -77.45, 311.68 ft
   distance: 0.18 miles
     hourly: 1973-01-01 - 2024-03-22
      daily: 1960-04-01 - 2024-12-30
    monthly: 1973-01-01 - 2024-03-22

KJYO0 Leesburg / Sycolin: 39.078, -77.5575, 390.42 ft
   distance: 11.53 miles
...

\"hourly\", \"daily\", and \"monthly\" refer to the date ranges for which data are available.

    \f
    Parameters
    ----------
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    """

    # If user entered city/state, convert to latitude/longitude first.
    if city != DEFAULT_CITY and state != DEFAULT_STATE:
        latitude, longitude = get_lat_long(city, state)

    stations_df: pd.DataFrame = get_nearby_stations(latitude, longitude)
    list_stations(stations_df)


todaydatetime: rd.datetime = rd.datetime.now()
todaynaive: rd.datetime = rd.tzdatetime_to_naivedatetime(todaydatetime)
is_leap_year: bool = int(TODAYS_DATE[:4]) % 4 == 0 and (int(TODAYS_DATE[:4]) % 100 != 0 or int(TODAYS_DATE[:4]) % 400 == 0)
days_in_year = 366 if is_leap_year else 365
# Get the datetime for one year ago
one_year_ago_datetime: rd.datetime = todaynaive - rd.timedelta(days=days_in_year)
one_year_ago: str = rd.datetime_to_datestr(one_year_ago_datetime, fmt="%Y-%m-%d")


@click.command(epilog="Example usage:\nsummary -lat 38.93485 -lon -77.44728 2020-01-01 2021-01-01\n")
# Default lat and lon is for Dulles International Airport, the closest
# meteorological station to McNair, VA
@click.option('-lat', "--latitude", type=float, default="38.93485", show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=float, default="-77.44728", show_default=True, help="Longitude for location.")
@click.option('-c', '--city', type=str, default=DEFAULT_CITY, show_default=True, help="City to get weather forecast for.")
@click.option('-s', '--state', type=str, default=DEFAULT_STATE, show_default=True, help="The city's state.")
@click.argument("startdate", required=True, default=one_year_ago)
@click.argument("enddate", required=True, default=TODAYS_DATE)
@click.pass_context
def summary(ctx, latitude, longitude, city, state, startdate, enddate) -> None:
    """
Print a table of summary statistics for the given date range. Default date range is the last 1 year time period. Sample table:

\b
Summary for Fairfax County, Virginia from 2023-03-01 to 2023-04-01\n

\b
        Avg Temp  Min temp  Max temp...
count      32.0      32.0      32.0...
mean       44.8      33.6      55.6...
std         7.3       7.0      10.0...
min        33.6      20.8      37.6...
max        62.4      47.7      79.7...

    \f
    Parameters
    ----------
    ctx : _type_ -- context
    latitude : float -- latitude of interest
    longitude : float -- longitude of interest
    city : str -- city of interest
    state : str -- state of interest
    startdate : str -- start date for weather data
    enddate : str -- end date for weather data
    """

    # Get the first weather station nearby the provided latitude/longitude.
    # Use that station's latitude, longitude, and elevation to instantiate a "Point" that
    # corresponds to the weather station's location.
    stations_df: pd.DataFrame = get_nearby_stations(latitude, longitude)
    dulles = Point(stations_df.iloc[0, 5], stations_df.iloc[0, 6], stations_df.iloc[0, 7])

    # Convert the start and end dates to naive datetimes.
    startdatetime: rd.datetime = rd.datestr_to_tzdatetime(startdate)
    start: rd.datetime = rd.tzdatetime_to_naivedatetime(startdatetime)
    enddatetime: rd.datetime = rd.datestr_to_tzdatetime(enddate)
    end: rd.datetime = rd.tzdatetime_to_naivedatetime(enddatetime)

    # Download the "Daily" data to a pandas DataFrame.
    summary_data = Daily(dulles, start, end)
    sdata: pd.DataFrame = summary_data.fetch()

    # Save the DataFrame to a CSV file in the USERPROFILE/Documents directory.
    save_pandas_data(sdata)

    # Convert columns from metric to imperial and round floats, as needed.
    sdata['tavg'] = sdata['tavg'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    sdata['tmin'] = sdata['tmin'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    sdata['tmax'] = sdata['tmax'].apply(lambda x: round((x * 9. / 5.) + 32., 1) if pd.notnull(x) else x)
    sdata['prcp'] = sdata['prcp'].apply(lambda x: round(x * 0.03937008, 2) if pd.notnull(x) else x)
    sdata['snow'] = sdata['prcp'].apply(lambda x: round(x * 0.03937008, 2) if pd.notnull(x) else x)
    sdata['wspd'] = sdata['wspd'].apply(lambda x: round(x * 0.62137119, 0) if pd.notnull(x) else x)
    sdata['pres'] = sdata['pres'].apply(lambda x: round(x * 0.750062, 1) if pd.notnull(x) else x)

    # Rename the columns to something more readable.
    sdata.columns = ["Avg Temp", "Min temp", "Max temp", "Rain", "Snow", "Wind Dir", "Wind Spd", "Wind gust", "Pressure", "Total Sun"]

    # Get summary data for most, but not all, of the columns (exclude "Wind gust" and "Total Sun").
    summary: pd.DataFrame = sdata.loc[:, ["Avg Temp", "Min temp", "Max temp", "Rain", "Snow", "Wind Dir", "Wind Spd", "Pressure"]].describe()

    # Round the summary data as appropriate.
    summary['Avg Temp'] = summary['Avg Temp'].round(1)
    summary["Min temp"] = summary['Min temp'].round(1)
    summary["Max temp"] = summary['Max temp'].round(1)
    summary["Rain"] = summary['Rain'].round(2)
    summary["Snow"] = summary['Snow'].round(2)
    summary["Wind Dir"] = summary['Wind Dir'].round().astype(int)
    summary["Wind Spd"] = summary['Wind Spd'].round().astype(int)
    summary["Pressure"] = summary['Pressure'].round(1)

    # Print a header before printing the data.
    city, state = get_location(stations_df.iloc[0, 5], stations_df.iloc[0, 6])
    print(f'\n[dark_orange]Summary for {city}, {state} from {startdate} to {enddate}[/]\n', sep="")

    # Rather than print the standard describe() dataframe, print just the data that I want.
    print(summary.loc[['count', 'mean', 'std', 'min', 'max']])

    return None


# ==== USER MANUAL ===========================================================

@click.group(invoke_without_command=True)
@click.option('-c', '--command', required=True, help="enter an available command", prompt="Command or \"manual\"")
# @click.version_option(version=VERSION)
@click.pass_context
def manual(ctx, command) -> None:
    """
Access information for specific commands. If "manual" is entered with no arguments, user will be prompted for a command.

\b
Available commands:
    coords
    location
    hourly-forecast
    rain-forecast
    alerts
    daily-summary
    meteostat
    single_day
    daily
    hourly
    monthly
    normals
    stations
    summary
    """

    # "manual.json" must exist in the same directory as "weather.py".
    # This file contains all the manual text in {dictionary} format.
    with open('manual.json', 'r') as file:
        data = json.load(file)

    if command.strip() in ["manual", "weather", "man", "help", "h"]:
        command = "cli"

    # If the user enters a bad command, print message and exit
    if command.strip() not in ["cli", "coords", "location", "hourly-forecast", "rain-forecast", "alerts", "daily-summary", "meteostat", "single_day", "daily", "hourly", "monthly", "normals", "stations", "summary"]:

        print('\nCommand not found.\nTry \"manual --help\" or \"manual -c man\" ')
        exit()

    print(f'{data[command]}')

    return None


cli.add_command(coords)
cli.add_command(location)
cli.add_command(alerts)
cli.add_command(rain_forecast)
cli.add_command(hourly_forecast)
cli.add_command(daily_summary)
cli.add_command(meteostat)
cli.add_command(manual)

meteostat.add_command(daily)
meteostat.add_command(single_day)
meteostat.add_command(hourly)
meteostat.add_command(monthly)
meteostat.add_command(normals)
meteostat.add_command(stations)
meteostat.add_command(summary)


# ==== GET, EXTRACT, & PRINT CURRENT OR FORECAST WEATHER =====================
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


def print_single_day(city, state, latitude, longitude, date, weather, feels_like, humidity, pressure, temperature, max_temp, min_temp, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow, alerts) -> None:
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
    if not (-90 <= lat <= 90):
        return False
    if not (-180 <= lon <= 180):
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
    with open(data_file, 'w') as file:
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
        with open(quote_file, 'r') as file:
            quote_data = json.load(file)
    else:
        print("\nAccessing zenquotes.io...")
        url = "https://zenquotes.io/api/quotes/"

        r = requests.get(url)
        if r.status_code != 200:
            print('\nCould not reach "https://zenquotes.io".', sep="")
            exit()

        quote_data = json.loads(r.text)

        with open(quote_file, 'w') as file:
            json.dump(quote_data, file, indent=4)

    random_quote_number = randint(0, len(quote_data) - 1)

    quote = quote_data[random_quote_number]["q"]
    print(f'\n[steel_blue1]{quote}[/]')

    print("[yellow2]Thanks for using this app. Give somone some love![/]")


if __name__ == '__main__':
    cli(obj={})

    # r_utils.print_documentation("C:\\Users\\rickr\\OneDrive\\Python on OneDrive\\Python CLI\\weather\\weather.py")
