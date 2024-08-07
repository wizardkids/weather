"""
    Filename: local.py
     Version: 0.1
      Author: Richard E. Rawson
        Date: 2024-07-15
 Description: Functions related to local weather.
"""

import configparser

import click
import requests
from utilities import rdatetime as rd
from utilities import utils

config = configparser.ConfigParser()
config.read(r'config.ini')
API_KEY: str = config['DEFAULT']['API_KEY']
DEFAULT_LAT: str = config['DEFAULT']['DEFAULT_LAT']
DEFAULT_LON: str = config['DEFAULT']['DEFAULT_LON']
DEFAULT_CITY: str = config['DEFAULT']['DEFAULT_CITY']
DEFAULT_STATE: str = config['DEFAULT']['DEFAULT_STATE']

# Create a naive date string for today's date in YYYY-MM-DD format.
todaydatetime: rd.datetime = rd.datetime.now()
todaynaive: rd.datetime = rd.tzdatetime_to_naivedatetime(todaydatetime)
TODAYS_DATE: str = rd.datetime_to_datestr(todaynaive, fmt="%Y-%m-%d")


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

    latitude, longitude = utils.get_lat_long(city, state)

    utils.get_weather_report(period, latitude, longitude, city, state, days)

    return None


@click.command(epilog='Use --period option to deliver either current or forecasted weather.\n\nIf an alert has been issued, that information is displayed without having to issue the "alerts" command.')
@click.option("-p", "--period", type=click.Choice(['current', 'forecast']), default='forecast', show_default=True, help="The time period for the report.")
@click.option('-lat', "--latitude", default=DEFAULT_LAT, type=click.FloatRange(min=-90.0, max=90.0), show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=click.FloatRange(min=-180.0, max=180.0), default=DEFAULT_LON, show_default=True, help="Longitude for location.")
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

    city, state = utils.get_location(latitude, longitude)

    utils.get_weather_report(period, latitude, longitude, city, state, days)

    return None


@click.command(epilog="--hours option can limit the number of hours reported. This report includes time, temperature, UVI, weather description, and chance of rain.")
@click.option('-lat', "--latitude", type=click.FloatRange(min=-90.0, max=90.0), default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=click.FloatRange(min=-180.0, max=180.0), default=DEFAULT_LON, show_default=True, help="Longitude for location.")
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
    if city != DEFAULT_CITY or state != DEFAULT_STATE:
        latitude, longitude = utils.get_lat_long(city, state)

    if utils.coord_arguments_ok(latitude, longitude):
        data = utils.get_hourly_forecast_data(latitude, longitude)

        utils.print_hourly_forecast(latitude, longitude, data, hours)

    else:
        error_msg = f'\nWe encountered an error with latitude={latitude} or longitude={longitude}. Either:\n   1. Latitude and/or longitude were entered as non-numbers.\n   2. Latitude and/or longitude were not in the ranges of -90 to 90 or -180 to 180, respectively.'
        print(f'[red1]{error_msg}[/]', sep="")


@click.command(epilog="Rain forecast is reported at 5 minute intervals for the next hour.")
@click.option('-lat', "--latitude", type=click.FloatRange(min=-90.0, max=90.0), default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=click.FloatRange(min=-180.0, max=180.0), default=DEFAULT_LON, show_default=True, help="Longitude for location.")
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
        latitude, longitude = utils.get_lat_long(city, state)

    if utils.coord_arguments_ok(latitude, longitude):
        data = utils.get_rain_forecast_data(latitude, longitude)

        utils.print_rain_forecast(latitude, longitude, data)

    else:
        error_msg = f'\nWe encountered an error with latitude={latitude} or longitude={longitude}. Either:\n   1. Latitude and/or longitude were entered as non-numbers.\n   2. Latitude and/or longitude were not in the ranges of -90 to 90 or -180 to 180, respectively.'
        print(f'[red1]{error_msg}[/]', sep="")


@click.command(epilog="If there is an alert, that information is included automatically in the current weather report (location or coords commands).")
@click.option('-lat', "--latitude", type=click.FloatRange(min=-90.0, max=90.0), default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=click.FloatRange(min=-180.0, max=180.0), default=DEFAULT_LON, show_default=True, help="Longitude for location.")
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
        latitude, longitude = utils.get_lat_long(city, state)

    if utils.coord_arguments_ok(latitude, longitude):

        city, state = utils.get_location(latitude, longitude)

        # "filter_times" are the periods to filter OUT.
        filter_times: str = "current,minutely,hourly,daily"
        data = utils.download_data(latitude, longitude, filter_times)

        # Check to see if there actually is an alert:
        try:
            sender = data['alerts'][0]["sender_name"]
        except KeyError:
            print(f'\n[dark_orange]No alerts have been issued for[/] [#d6d9fe]{city}, {state}[/]', sep="")
            return None

        utils.print_alerts(city, state, data)

    else:
        error_msg = f'\nWe encountered an error with latitude={latitude} or longitude={longitude}. Either:\n   1. Latitude and/or longitude were entered as non-numbers.\n   2. Latitude and/or longitude were not in the ranges of -90 to 90 or -180 to 180, respectively.'
        print(f'[red1]{error_msg}[/]', sep="")


@click.command(epilog="A daily summary provides summary data for a day's worth of weather information. For example, temperature would represent the average temperature for the day and precipitation reports to total rainfall for the day.")
@click.option('-lat', "--latitude", type=click.FloatRange(min=-90.0, max=90.0), default=DEFAULT_LAT, show_default=True, help="Latitude for location.")
@click.option('-lon', '--longitude', type=click.FloatRange(min=-180.0, max=180.0), default=DEFAULT_LON, show_default=True, help="Longitude for location.")
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
        latitude, longitude = utils.get_lat_long(city, state)

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
    utils.save_data(data)

    city, state = utils.get_location(latitude, longitude)

    utils.print_daily_summary(latitude, longitude, city, state, data)

    return None
