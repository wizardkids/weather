"""
    Filename: manual.py
     Version: 0.1
      Author: Richard E. Rawson
        Date: 2024-03-28
 Description: Dictionary that forms the basis for the manual associated with weather.py.

When this .py file is run, {manual_info}, is saved in json format. When the user wants to retrieve information from the command line about a command, say "weather.py manual coords", the json file is read into a python dictionary, and the value for the "coords" key is printed in the terminal.

 {manual_info} is based on docstrings, but contains additional information that is reorganized to be more "manual-like".

 NOTE that docstrings are saved in docstrings.json, a file that is created by r_utils.print_documentation().
"""

import json

manual_info: dict[str, str] = {
    "cli": """
[yellow1]NAME:[/]
[light_steel_blue1]weather - retrieve weather reports[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]weather [--version] [--help] <command>[/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Display weather reports or alerts for location (city/state) or coords(latitude/longitude). Every time a report is run, data are saved to "USERPROFILE/downloads/data.json" (or "USERPROFILE/downloads/weather_data.csv" for meteostat data).

This weather app is replete with defaults. Executing the app with no arguments is the same as:[/]

    [dark_orange]coords -p current -lat (default lat) -lon (default lon)[/]

[light_steel_blue1]Defaults can only be customized by editing the source code. Currently, any time a command is issued without lat/lon or city/state, these are the values that are used:[/]

    [dark_orange]DEFAULT_LAT: str = "38.95669"
    DEFAULT_LON: str = "-77.41006"
    DEFAULT_CITY: str = "Herndon"
    DEFAULT_STATE: str = "Virginia"[/]

[light_steel_blue1]The --period option, which allows for selection of either the current or forecasted weather, is only valid for the "coords" and "location" commands.

To get the current weather for the default location, use the "coords" or "location" commands without arguments. "coords" uses the DEFAULT_LAT/DEFAULT_LON (McNair, VA; 38.95669, -77.41006) and "location" uses DEFAULT_CITY/DEFAULT_STATE (Herndon, VA; 38.9695316, -77.3859479)

Data are downloaded from openweathermap.org or meteostat.net.[/]

[yellow1]COMMANDS ORGANIZED BY PERIOD:[/][light_steel_blue1]

[yellow1]Today's current or forecasted weather[/]
    location        Current or forecasted weather
    coords          Current or forecasted weather
    alerts          Currently issued weather alerts

[yellow1]Detailed weather[/]
    hourly-forecast Hourly forecast for up to 48 hours
    rain-forecast   Rain for next hour

[yellow1]Weather summaries[/]
    daily-summary   Mean or total values on the provided [DATE]
    meteostat
        single-day  Data for a specific day and time
        daily       Data in daily increments
        hourly      Data  in hourly increments
        monthly     Data  in monthly increments
        summary     summary statistics for variables between two dates
        normals     Normal weather data for 30-year period
        stations    Five meteorological stations nearest to a location

[yellow1]manual[/]              Access this user manual
[/]
    """,
    "coords": """
[yellow1]NAME:[/]
[light_steel_blue1]coords - weather for lat/lon[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]coords [-p | --period] [-d | --days] [-lat | --latitude] [-lon | --longitude] [--help][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Current or forecasted weather for the provided location. This command only takes latitude and longitude as arguments and not city/state.

Forecast weather is default; current weather can be retrieved using the "-p current" option. "--days" determines how many days are included in the forecast. Today and tomorrow is the default. One week (8 days) is the max. [Forecast weather can also be retrieved with "-p forecast" but, given default settings, this is not necessary.]

Alerts are included if any alerts have been issued for the provided location.[/]

[yellow1]EXAMPLE USAGE:[/]
    [dark_orange]coords[/] [light_steel_blue1]--> forecast weather for default latitude and longitude for two days[/]

    [dark_orange]coords -p forecast -lat 42.4372 -lon -76.5484[/] [light_steel_blue1]--> 8-day forecast for this latitude/longitude[/]

[yellow1]EXAMPLE DATA:[/]
    [dark_orange]coords -p current -lat 38.9695316 -lon -77.3859479[/]

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
    """,
    "location": """
[yellow1]NAME:[/]
[light_steel_blue1]location - weather for city/state[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]location [-p | --period] [-d | --days] [-c | --city] [-s | --state] [--help][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Current or forecasted weather for the provided location. This command only takes city and state as arguments and not latitude/longitude.

Forecast weather is default; current weather can be retrieved using the "-p current" option. "--days" determines how many days are included in the forecast. Today and tomorrow is the default. One week (8 days) is the max. [Forecast weather can also be retrieved with "-p forecast" but, given default settings, this is not necessary.]

Alerts are included if any alerts have been issued for the provided location.[/]

[yellow1]EXAMPLE USAGE:[/]
    [dark_orange]location[/] [light_steel_blue1]--> forecast weather for default city and state[/]

    [dark_orange]location -p current --city Ithaca --state "New York"[/] [light_steel_blue1]--> current weather for Ithaca, NY[/]

[yellow1]EXAMPLE DATA: [/]
    [dark_orange]location -c Alexandria -s Virginia[/]

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
    """,
    "hourly-forecast": """
[yellow1]NAME:[/]
[light_steel_blue1]hourly-forecast - weather on the hour[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]hourly-forecast [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [-h | --hours] [--help][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Forecast for the provided location, hourly. This command uses the default lat/lon and a time period of 8 hours if no arguments are entered. Location can be identified either by lat/lon or by city/state. Maximum number of hours is 48.[/]

[yellow1]EXAMPLE USAGE:[/]
    [dark_orange]hourly-forecast[/] [light_steel_blue1]--> next 8 hours forecast for default location[/]

    [dark_orange]hourly-forecast --lat (default lat) --lon (default lon) --hours 24[/]

[yellow1]EXAMPLE DATA: hourly-forecast -h 4[/]

Hourly forecast for McNair, Virginia

Wednesday, Mar 27, 2024
           03:00 PM                      04:00 PM                      05:00 PM
       overcast clouds               overcast clouds               overcast clouds
     Temperature: 47 °F            Temperature: 47 °F            Temperature: 47 °F
            rain: 0.00 in.                rain: 0.00 in.                rain: 0.00 in.
             UVI: 0.62                     UVI: 0.4                      UVI: 0.49
  Chance of rain: 35.0 %        Chance of rain: 51.0 %        Chance of rain: 69.0 %

           06:00 PM
          light rain
     Temperature: 46 °F
            rain: 0.02 in.
             UVI: 0.23
  Chance of rain: 92.0 %
    """,
    "rain-forecast": """
[yellow1]NAME:[/]
[light_steel_blue1]rain-forecast - one-hour rain forecast[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]rain-forecast [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Rain for next hour in 5-min intervals for the provided location. This command uses the default lat/lon if no arguments are entered. Location can be identified either by lat/lon or by city/state.

The total amount of precipitation expected over the next hour is also provided. Decimal precision (4 decimal places) reflects the fact that downloaded data reports amounts with 4 decimals. Note that this means very short bursts of light rain can be included in predictions... a notable benefit of this report![/]

[yellow1]EXAMPLE USAGE:[/]
    [dark_orange]rain-forecast[/] [light_steel_blue1]--> forecast for default location for the next hour[/]

    [dark_orange]rain_forecast --lat (default lat) --lon (default lon)[/]

[yellow1]EXAMPLE DATA: rain-forecast (no arguments)[/]

    Expected rainfall in the next hour
    2024-03-26 -- McNair, Virginia

    03:24: 0.0000 in.
    03:29: 0.0000 in.
    03:34: 0.0000 in.
    03:39: 0.0000 in.
    03:44: 0.0000 in.
    03:49: 0.0042 in.
    03:54: 0.0110 in.
    03:59: 0.0124 in.
    04:04: 0.0000 in.
    04:09: 0.0000 in.
    04:14: 0.0000 in.
    04:19: 0.0000 in.
    Total expected precipitation: 0.0276 in.
    """,
    "alerts": """
[yellow1]NAME:[/]
[light_steel_blue1]alerts - current weather alerts[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]alerts [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Currently issued weather alerts for the provided location. This command uses the default lat/lon if no arguments are entered. Location can be identified either by lat/lon or by city/state.

Alerts are automatically included with current weather and forecasts ("coords" or "location") if any alerts have been issued.[/]

[yellow1]EXAMPLE USAGE:[/]
    [dark_orange]alerts[/] [light_steel_blue1]--> current alerts for the provided location[/]

[yellow1]EXAMPLE DATA: [/]
    [dark_orange]alerts (no arguments)[/]

    ALERT from NWS Baltimore MD/Washington DC
    for McNair, Virginia
    starts: Tuesday, 07:00 PM
    end: Wednesday, 03:00 PM

    Coastal Flood Advisory
    * WHAT...Up to one half foot of inundation above ground level expected in low lying areas due to tidal flooding.

    * WHERE...Fairfax, Stafford and Southeast Prince William Counties.
    ...
    """,
    "daily-summary": """
[yellow1]NAME:[/]
[light_steel_blue1]daily-summary - summary of one day's weather[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]daily-summary [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help] [DATE][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Report mean or total values for the provided location on [DATE]. This command uses the default lat/lon and today's date if no arguments are entered. Location can be identified either by lat/lon or by city/state. Any date from 1st January 1979 till 4 days ahead forecast can be used.

Dates can be entered in any of a variety of formats, including "YYYY-MM-DD" and "MM-DD-YYYY". Because this command delivers a summary weather report for a day, time is irrelevant.[/]

[yellow1]EXAMPLE USAGE:[/]
    [dark_orange]daily-summary -c Herndon -s Virginia 2023-03-20[/]

[yellow1]EXAMPLE DATA:[/]
    [dark_orange]daily-summary 2023-03-20[/]

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
    """,
    "meteostat": """
[yellow1]NAME:[/]
[light_steel_blue1]meteostat - access bulk weather data[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]meteostat [--version] [--help] <commands>[/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Report bulk meteorological data for a variety of periods. Latitude and longitude default to Dulles International Airport. Data are saved in "USERPROFILE/downloads/weather_data.csv" after each report is run.

Data are downloaded from meteostat.net, with the exception of "single-day" that gets data from openweathermap.org.[/]

[yellow1]COMMANDS:[/][light_steel_blue1]
    [royal_blue1]single-day[/]
        Data for a specific day and time (default time: 12:00pm)
    [royal_blue1]daily[/]
        Data are reported in daily increments.
    [royal_blue1]hourly[/]
        Data are reported in hourly increments.
    [royal_blue1]monthly[/]
        Data are reported in monthly increments.
    [royal_blue1]summary[/]
        count, mean, std dev, min, and max values for weather variable
        between provided dates.
    [royal_blue1]normals[/]
        Normal weather data for 30-year period reported as average values
        for each of 12 months.
    [royal_blue1]stations[/]
        List five meteorological stations nearest to the provided
        latitude/longitude.
    [/]
    """,
    "single_day": """
[yellow1]NAME:[/]
[light_steel_blue1]single-day - weather for a single day[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]single-day [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help] [DATE][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Report weather for the provided [DATE]. [DATE] must be on or after Jan 1, 1979 and up to 4 days from today's date. See epilog for formatting [DATE].

[DATE] can include a time-of-day. If no time is included in the submitted [DATE], the 12:00 pm will be used by default. Dates can be entered in any of a variety of formats, including "YYYY-MM-DD H:M" and "MM-DD-YYYY H:M". Time can be entered as 12- or 24 hour clock, for example "06:00 pm" or "18:00". If a time is included, the space requires that the whole date/time string be enclosed in quotes.

Data are downloaded from openweathermap.org.[/]

[yellow1]Example data: [/]
    [dark_orange]meteostat single-day "2023-03-01 07:00"[/]

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

    """,
    "daily": """
[yellow1]NAME:[/]
[light_steel_blue1]daily - summary weather each day between two dates[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]single-day [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help] [STARTDATE] [ENDDATE][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Report mean or total weather data for each day between two dates, inclusive. Default dates: 1960-01-01 to today.

Dates can be entered in any of a variety of formats, including "YYYY-MM-DD" and "MM-DD-YYYY". Because this command delivers a summary weather report for a day, time is irrelevant.[/]

[yellow1]EXAMPLE DATA: [/]
    [dark_orange]meteostat daily 2023-03-01 2023-03-03[/]

            Avg temp  Min temp  Max temp  Rain  Snow  Wind Dir  Wind Spd  Pressure
time
2023-03-01      44.2      27.9      59.7  0.00   0.0     163.0       7.0     761.9
2023-03-02      52.7      40.6      63.7  0.01   0.0     328.0       7.0     755.5
2023-03-03      41.9      36.7      45.7  0.56   0.0      62.0       7.0     758.1
    """,
    "hourly": """
[yellow1]NAME:[/]
[light_steel_blue1]hourly - hourly weather between two dates[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]hourly [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help] [STARTDATE] [ENDDATE][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Get weather data every hour between two dates. Default dates: 1973-01-01 to today. See CAUTION below.

[STARTDATE] and/or [ENDDATE] can include a time-of-day. If no time is included in the submitted [STARTDATE] and [ENDDATE], then 12:00 am will be used by default, resulting in 24 hours of data for each day included between [STARTDATE] and [ENDDATE], inclusive. Dates can be entered in any of a variety of formats, including "YYYY-MM-DD H:M" and "MM-DD-YYYY H:M". Time can be entered as 12- or 24 hour clock, for example "06:00 pm" or "18:00".

CAUTION: Using default dates is not recommended. Accessing the 438,000 hours associate with using these dates takes a considerable amount of time.[/]

[yellow1]EXAMPLE DATA: [/]
    [dark_orange]meteostat hourly 2023-03-01 2023-03-03[/]

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
    """,
    "monthly": """
[yellow1]NAME:[/]
[light_steel_blue1]monthly - first-of-the-month weather between two dates[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]monthly [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help] [STARTDATE] [ENDDATE][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Report first-of-the-month weather data between two dates. Default dates: 1960-01-01 to today.

[STARTDATE] and [ENDDATE] can be entered in any of a variety of formats, including "YYYY-MM-DD" and "MM-DD-YYYY". Since data are reported for the whole day, on the first of each month, time is irrelevant.[/]

[yellow1]EXAMPLE DATA:[/]
    [dark_orange]meteostat monthly 2023-03-01 2023-06-01[/]

    Fairfax County, Virginia
    Station: Dulles International Airport
    Weather data for 2023-03-01 to 2023-06-01
    Latitude: 38.9333, Longitude: -77.45


                Mean Temp: 57.98 °F
         Highest max Temp: 55.90 °F
          Lowest min Temp: 55.00 °F
            Mean Wind Spd: 8 mph
             Max Wind Spd: 9 mph
             Min Wind Spd: 6 mph
            Mean pressure: 761.10 in.
    Mean monthly rainfall: 2.16 in.
           Total rainfall: 8.65 in.


            Avg Temp  Min Temp  Max Temp  Precipitation  Wind spd  Pressure
time
2023-03-01      44.2      33.3      55.0           1.57       9.0       NaN
2023-04-01      58.1      43.3      70.3           3.30       8.0     762.1
2023-05-01      60.3      47.3      72.3           1.48       6.0     762.8
2023-06-01      69.3      55.9      80.6           2.30       7.0     758.4
    """,
    "normals": """
[yellow1]NAME:[/]
[light_steel_blue1]normals - normal weather values[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]normals [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help] [STARTDATE] [ENDDATE][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Normals for the provided location calculated over 30 years. Default is 1991 to 2020.

Data for a variety of variables is averaged over the 30-year period for each of the 12 months of the year. Hence, the returned table will include average data for January over the 30 years, and so on.

The earliest data available is 1961. It is highly recommended that the default dates be used because the criteria for valid dates is very rigid:

    Criteria for the date range:
            1. Both start and end year are required.
            2. end - start must equal 29.
            3. end must be an even decade (e.g., 1990, 2020)
            4. end must be earlier than the current year

If default dates are used then using the command "normals" without arguments will return normal weather values for the default lat/lon.[/]

[yellow1]EXAMPLE DATA:[/]
    [dark_orange]normals[/]

       Avg Temp  Min temp  Max temp  Precip  Wind Spd  Pressure  Total Sun
month
1          -0.2      -5.2       4.7    74.5      12.6    1019.8        NaN
2           1.2      -4.3       6.6    64.3      13.0    1018.4        NaN
3           5.5      -0.5      11.5    89.0      13.8    1017.2        NaN

    """,
    "stations": """
[yellow1]NAME:[/]
[light_steel_blue1]stations - list meteorological station[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]station [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]List meteorological stations nearby to the provided location. At most, five stations will be listed.

As a programming note, if the entered lat/lon is used for other "meteostat" reports, the first station in the list is used as the source of weather data.[/]

[yellow1]EXAMPLE DATA: [/]
    [dark_orange]meteostat stations -lat 38.9695316 -lon -77.3859479[/]

72403 Dulles International Airport: 38.9333, -77.45, 311.68 ft
   distance: 0.18 miles
     hourly: 1973-01-01 - 2024-03-22
      daily: 1960-04-01 - 2024-12-30
    monthly: 1973-01-01 - 2024-03-22

KJYO0 Leesburg / Sycolin: 39.078, -77.5575, 390.42 ft
   distance: 11.53 miles
...

"hourly", "daily", and "monthly" in the list above refer to the date ranges for which data are available.
    """,
    "summary": """
[yellow1]NAME:[/]
[light_steel_blue1]summary - summary statistics for a date range[/]

[yellow1]SYNOPSIS:[/]
[light_steel_blue1]normals [-lat | --latitude] [-lon | --longitude] [-c | --city] [-s | --state] [--help] [STARTDATE] [ENDDATE][/]

[yellow1]DESCRIPTION:[/]
[light_steel_blue1]Print a table of summary statistics for the given date range. Default date range is the last 1 year time period.

Dates can be entered in any of a variety of formats, including "YYYY-MM-DD" and "MM-DD-YYYY". Because this command delivers a report of aggregated data, time is irrelevant.[/]

[yellow1]EXAMPLE DATA: [/]
    [dark_orange]meteostat summary[/]

Summary for Fairfax County, Virginia from 2023-03-01 to 2023-04-01

       Avg Temp  Min temp  Max temp    Rain    Snow  Wind Dir  Wind Spd  Pressure
count     367.0     367.0     367.0  367.00  367.00       366       367     366.0
mean       56.5      44.7      67.7    0.11    0.00       217         6     762.4
std        15.2      15.3      16.5    0.30    0.01       121         3       5.4
min        17.2       4.8      23.9    0.00    0.00         0         1     746.8
max        83.8      71.6      97.7    2.15    0.08       359        20     778.7
    """
}

# for k, v in manual.items():
#     print(k, v)

with open("manual.json", 'w') as file:
    json.dump(manual_info, file, indent=4)
    print("\nUpdated manual.json.")
