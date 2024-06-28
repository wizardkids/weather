"""
    Filename: meteostat_lib.py
     Version: 1.0
      Author: Richard E. Rawson
        Date: 2024-06-28
 Description: Functions related to the Meteostat API.
"""

import configparser

import click
import pandas as pd
import rdatetime as rd
from icecream import ic
from meteostat import Daily, Hourly, Monthly, Normals, Point
from rich import print
import utils

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


@click.group(invoke_without_command=True, epilog="Data are based on the weather station closest to the provided latitude/longitude. Use \"meteostat stations\" to list the five closest stations.")
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
        latitude, longitude = utils.get_lat_long(city, state)

    if len(date) == 10:
        date += " 12:00"

    localdatetime: rd.datetime = rd.datestr_to_tzdatetime(date)
    UTCts: int = int(rd.datetime_to_ts(localdatetime))

    # Make sure provided date is after 01-01-1979.
    if not utils.is_single_day_date_ok(UTCts):
        print(f'\nProvided date \"{date}\" must be on or after \"01-01-1979\" but no later than 4 days from today.', sep="")
        exit()

    # Find the corresponding city/state for the provide lat/lon.
    city, state = utils.get_location(latitude, longitude)

    # Retrieve the data from openweathermap.org for the provided date.
    data = utils.get_single_day_data(latitude, longitude, UTCts)

    # From the downloaded data, get the variables we want.
    date, weather, feels_like, humidity, pressure, temperature, max_temp, min_temp, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow = utils.extract_single_day_weather_vars(data)

    # Print the final report.
    utils.print_single_day(city, state, latitude, longitude, date, weather, feels_like, humidity, pressure, temperature, max_temp, min_temp, visibility, wind_direction, wind_speed, sunrise, sunset, gust, uvi, dew_point, rain, snow)

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
    stations_df: pd.DataFrame = utils.get_nearby_stations(latitude, longitude)
    dulles = Point(stations_df.iloc[0, 5], stations_df.iloc[0, 6], stations_df.iloc[0, 7])

    weather_station = stations_df.iloc[0, 0]

    city, state = utils.get_location(latitude, longitude)

    startdatetime: rd.datetime = rd.datestr_to_tzdatetime(startdate)
    start: rd.datetime = rd.tzdatetime_to_naivedatetime(startdatetime)
    enddatetime: rd.datetime = rd.datestr_to_tzdatetime(enddate)
    end: rd.datetime = rd.tzdatetime_to_naivedatetime(enddatetime)

    # Get daily data for period
    # daily_data = Daily(stations_df.index[0])
    daily_data = Daily(dulles, start, end)
    ddata: pd.DataFrame = daily_data.fetch()

    # Save the raw downloaded data.
    utils.save_pandas_data(ddata)

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

    stations_df: pd.DataFrame = utils.get_nearby_stations(latitude, longitude)

    # Get the name of the weather station.
    weather_station = stations_df.iloc[0, 0]

    city, state = utils.get_location(stations_df.iloc[0, 5], stations_df.iloc[0, 6])

    # Get the first weather station nearby the provided latitude/longitude.
    # Use that station's latitude, longitude, and elevation to instantiate a "Point" that
    # corresponds to the weather station's location.

    hourly_data = Hourly(stations_df.index[0], start, end)
    hdata: pd.DataFrame = hourly_data.fetch()

    # Save the raw downloaded data.
    utils.save_pandas_data(hdata)

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
    stations_df: pd.DataFrame = utils.get_nearby_stations(latitude, longitude)
    dulles = Point(stations_df.iloc[0, 5], stations_df.iloc[0, 6], stations_df.iloc[0, 7])

    # Get the first weather station in stations_df. This is the closest station to lat/lon.
    weather_station = stations_df.iloc[0, 0]

    city, state = utils.get_location(stations_df.iloc[0, 5], stations_df.iloc[0, 6])

    startdatetime: rd.datetime = rd.datestr_to_tzdatetime(startdate)
    start = rd.tzdatetime_to_naivedatetime(startdatetime)
    enddatetime: rd.datetime = rd.datestr_to_tzdatetime(enddate)
    end = rd.tzdatetime_to_naivedatetime(enddatetime)

    # Download monthly data.
    monthly = Monthly(dulles, start, end)
    mdata: pd.DataFrame = monthly.fetch()

    # Save the DataFrame to a CSV file in the USERPROFILE/Documents directory.
    utils.save_pandas_data(mdata)

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
    stations_df: pd.DataFrame = utils.get_nearby_stations(latitude, longitude)
    dulles = Point(stations_df.iloc[0, 5], stations_df.iloc[0, 6], stations_df.iloc[0, 7])

    # Get normal values from 1991 to 2020.
    normals = Normals(dulles, 1991, 2020)
    ndata: pd.DataFrame = normals.fetch()

    # Save the DataFrame to a CSV file in the USERPROFILE/Documents directory.
    utils.save_pandas_data(ndata)

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
        latitude, longitude = utils.get_lat_long(city, state)

    stations_df: pd.DataFrame = utils.get_nearby_stations(latitude, longitude)
    utils.list_stations(stations_df)


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
    stations_df: pd.DataFrame = utils.get_nearby_stations(latitude, longitude)
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
    utils.save_pandas_data(sdata)

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
    city, state = utils.get_location(stations_df.iloc[0, 5], stations_df.iloc[0, 6])
    print(f'\n[dark_orange]Summary for {city}, {state} from {startdate} to {enddate}[/]\n', sep="")

    # Rather than print the standard describe() dataframe, print just the data that I want.
    print(summary.loc[['count', 'mean', 'std', 'min', 'max']])

    return None


# ==== END OF METEOSTAT FUNCTIONS ============================================

if __name__ == '__main__':
    pass
