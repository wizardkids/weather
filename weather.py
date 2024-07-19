"""
    Filename: weather.py
     Version: 2.0
      Author: Richard E. Rawson
        Date: 2024-03-08
 Last update: 2024-07-15
 Description: Print weather reports to the terminal.

Modules:
    weather -- current and forecasted weather reports
    meteostat_lib -- meteostat library functions
    utils -- 31 functions that get, extract, & print current or forecast weather
    local -- functions that get current and forecast weather for a locality


~CUSTOMIZATION:
Customizing defaults is done by editing the config.ini file.

RESOURCES:
    https://openweathermap.org/api
    https://openweathermap.org/api/geocoding-api
    https://home.openweathermap.org/statistics/onecall_30 --> for my usage statistics

    https://dev.meteostat.net/python/

-- PROGRAMMING NOTE:
    ! Dates can be entered by user as timezone-unaware dates, but within code, dates are almost always UTC, except where printed to the terminal where the UTC date is converted to the local time zone.
"""

import configparser
import json
import warnings

import click
# from icecream import ic
from rich import print
from utilities import local, meteostat_lib
from utilities import rdatetime as rd
from utilities import utils
from utilities.meteostat_lib import (daily, hourly, monthly, normals,
                                     single_day, stations, summary)

warnings.filterwarnings('ignore', category=FutureWarning)

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY: str = config['DEFAULT']['API_KEY']
DEFAULT_LAT: str = config['DEFAULT']['DEFAULT_LAT']
DEFAULT_LON: str = config['DEFAULT']['DEFAULT_LON']
DEFAULT_CITY: str = config['DEFAULT']['DEFAULT_CITY']
DEFAULT_STATE: str = config['DEFAULT']['DEFAULT_STATE']
VERSION = "2.0"


# Create a naive date string for today's date in YYYY-MM-DD format.
todaydatetime: rd.datetime = rd.datetime.now()
todaynaive: rd.datetime = rd.tzdatetime_to_naivedatetime(todaydatetime)
TODAYS_DATE: str = rd.datetime_to_datestr(todaynaive, fmt="%Y-%m-%d")


# CODENOTE If "invoke_without_command" is false, then running weather.py without arguments is the same as weather.py --help. If set to True, cli() executes in all circumstances. If weather.py is run with no arguments, then an if statement will run "coords -p forecast -lat <default lat> -lon <default lon>".

@click.group(invoke_without_command=True, epilog='Except \"meteostat\", using commands without arguments retrieves weather data for \"today\" at lat/lon =[DEFAULT_LAT, DEFAULT_LON] or city/state = [DEFAULT_CITY, DEFAULT_STATE]. These commands aim to provide weather information for the immediate time period. \n\n\"meteostat\" exposes 6 subcommands for accessing ranges of weather data in bulk, from a single day/time to one-day-a-month over 30 years. Bulk data are saved to file in the user\'s \"Downloads\" directory for analysis by other programs.')
@click.version_option(version=VERSION)
@click.pass_context
def cli(ctx) -> None:
    """
    Display weather reports or alerts for location (city/state) or coords (latitude/longitude). This weather app is replete with defaults. Executing the app with no arguments is the same as:

    coords -p forecast -lat <default lat> -lon <default lon>

    \b
    Further, every command has similar defaults, as needed.
    See "<command> --help" for any command for details.
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
        city, state = utils.get_location(latitude, longitude)

        utils.get_weather_report('forecast', latitude, longitude, city, state, days=2)


# ==== USER MANUAL ===========================================================

@click.group(invoke_without_command=True)
@click.option('-c', '--command', required=True, help="enter an available command", prompt="Command or \"manual\"")
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

    # This file contains all the manual text in {dictionary} format.
    with open('utilities/manual.json', 'r') as file:
        data = json.load(file)

    if command.strip() in ["manual", "weather", "man", "help", "h"]:
        command = "cli"

    # If the user enters a bad command, print message and exit
    if command.strip() not in ["cli", "coords", "location", "hourly-forecast", "rain-forecast", "alerts", "daily-summary", "meteostat", "single_day", "daily", "hourly", "monthly", "normals", "stations", "summary"]:

        print('\nCommand not found.\nTry \"manual --help\" or \"manual -c man\" ')
        exit()

    print(f'{data[command]}')

    return None


cli.add_command(local.coords)
cli.add_command(local.location)
cli.add_command(local.alerts)
cli.add_command(local.rain_forecast)
cli.add_command(local.hourly_forecast)
cli.add_command(local.daily_summary)
cli.add_command(meteostat_lib.meteostat)
cli.add_command(manual)

meteostat_lib.meteostat.add_command(daily)
meteostat_lib.meteostat.add_command(single_day)
meteostat_lib.meteostat.add_command(hourly)
meteostat_lib.meteostat.add_command(monthly)
meteostat_lib.meteostat.add_command(normals)
meteostat_lib.meteostat.add_command(stations)
meteostat_lib.meteostat.add_command(summary)


if __name__ == '__main__':
    cli(obj={})
