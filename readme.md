# Weather CLI

This Python script is a command-line interface (CLI) tool that retrieves weather information for a specified location. It uses the [OpenWeatherMap API](https://openweathermap.org/api) to fetch current and forecasted weather data and the [meteostat library](https://dev.meteostat.net/python/) for time series (historical) weather data.

## Prerequisites
Before running this script, you need an API key from OpenWeatherMap. You can sign up for a free account at [https://openweathermap.org/api](https://openweathermap.org/api).

Change the name of the config.ini.template file to config.ini and then edit the file, inserting your API key and location data in the obvious locations.

## Help

The weather app provides extensive information, requiring that the CLI be somewhat robust. A manual provides complete information for each option, arguments, and commands.

`python weather.py manual`

CLI help is available for the main app as well as many commands. For example:

`python weather.py --help`</br>
`python weather.py location --help`</br>
`python weather.py daily-summary --help`

## Usage
```
Usage: weather.py [OPTIONS] COMMAND [ARGS]...

  Display weather reports or alerts for location (city/state) or coords
  (latitude/longitude). This weather app is replete with defaults. Executing
  the app with no arguments is the same as:

  coords -p forecast -lat (default lat) -lon (default lon)

  Further, every command has similar defaults, as needed.
  See <command> --help for each command for details.
  Example: python weather.py location --help

  Commands organized by period:

  Today's current or forecasted weather
      location        Current or forecasted weather
      coords          Current or forecasted weather
      alerts          Currently issued weather alerts

  Detailed weather
      hourly-forecast Hourly forecast for up to 48 hours
      rain-forecast   Rain for next hour

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

  manual              Access this user manual

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  alerts           Currently issued weather alerts.
  coords           Current or forecasted weather.
  daily-summary    Report mean or total values for the provided [DATE].
  hourly-forecast  Forecast for the provided location, hourly.
  location         Current or forecasted weather.
  manual           Access information for specific commands.
  meteostat        Report bulk meteorological data for a variety of periods.
  rain-forecast    Rain for next hour in 5-min intervals.

  Except "meteostat", using commands without arguments retrieves weather data
  for "today" at lat/lon =[DEFAULT_LAT, DEFAULT_LON] or city/state =
  [DEFAULT_CITY, DEFAULT_STATE]. These commands aim to provide weather
  information for the immediate time period.

  "meteostat" exposes 6 subcommands for accessing ranges of weather data in
  bulk, from a single day/time to one-day-a-month over 30 years. Bulk data are
  saved to file in the user's "Downloads" directory for analysis by other
  programs.
```

## Example Usage
`python weather.py` --> forecast for today and tomorrow, with any alerts

`python weather.py coords -d 4 -p forecast` --> 4 day forecast

`python weather.py hourly-forecast -h 12` --> hourly forecast for next 12h

`python weather.py coords -p current` --> current weather at default lat/long

`python weather.py location -p forecast -c Alexandria -s Virginia` --> forecast</br> for the specified location

`python weather.py meteostat --help` --> help for meteostat subcommands

`python weather.py meteostat stations` --> 5 closest weather stations

`python weather.py meteostat hourly 2024-06-15 2024-06-16` --> hourly data</br>between two dates

## Notes
- Default coordinates (latitude and longitude) and location (city and state)</br>
are kept in the config.ini file.
- All weather data is limited to the United States only. International weather</br>is not available.

## Dependencies
- [click](https://click.palletsprojects.com/en/8.1.x/) (for command-line interface)
- [pandas](https://pandas.pydata.org/docs/index.html)
- [requests](https://requests.readthedocs.io/en/latest/)
- [meteostat](https://dev.meteostat.net/python/)
- [rich](https://rich.readthedocs.io/en/latest/)