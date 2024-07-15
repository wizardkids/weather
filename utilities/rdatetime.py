"""
    Filename: rdatetime.py
     Version: 0.1
      Author: Richard E. Rawson
        Date: 2024-03-19
 Description: Provide a variety of convenience methods for inter-converting date strings, datetime objects, and timestamps.

- All functions that take a date as a string require an "input_fmt" that is the format of the string being passed in. If the format of the string is DEFAULT_FMT, then "input_fmt" does not need to be specified.

- All functions that return a date string require an "output_fmt" that is the format of the date being returned. If the format of the returned date is DEFAULT_FMT, then "output_fmt" does not need to be specified.

- Most functions are capable of changing time zones. As an example, it is possible to pass in a datetime object in the "US/Eastern" timezone and return a date string where the time is adjusted for "US/Central".

- If the need is to simply convert between date types and you are using DEFAULT_FMT and DEFAULT_TZ, then all functions can simply take a datetime object or a date string, with no other arguments and return a converted object.

For a list of all timezones, use:
    from zoneinfo import available_timezones
    timezones = available_timezones()

- Naming conventions:
    - "tz" prefix emphasizes that the function takes a timezone-aware object.

    EXAMPLES:
    - datestr_to_tzdatetime -->
            take any date string and convert it to a timezone-aware datetime object

    - tzdatetime_to_naivedatetime -->
            take any timezone-aware datetime object and convert it to a timezone-naive datetime object

- It is easy to add functionality to this module, as needed. Significant effort has been applied to naming of functions and variables so what they represent is as obvious as possible and internally consistent.

METHODS:
      datestr_to_tzdatetime -- any date or date/time string into a tz-aware datetime object
tzdatetime_to_naivedatetime -- tz-aware datetime to a naive datetime
        datetime_to_datestr -- any datetime to a formatted date string
           change_timezones -- change datetime from source-tz to target-tz
             datetime_to_ts -- any datetime to (UTC) timestamp
              datestr_to_ts -- any date string to (UTC) timestamp
             ts_to_datetime -- UTC timestamp to a datetime object in target tz
              ts_to_datestr -- UTC timestamp to a formatted date string in target tz
            datetime_to_dow -- day of week as DDD or full name
          datetime_to_month -- month name as MMM or full name
"""

# timedelta provided for convenience in programs that import this module.
from datetime import datetime, timedelta, timezone

import pytz
# requires: pip install python-dateutil
from dateutil import parser
from dateutil.parser import ParserError
# from icecream import ic
import calendar

# from utilities import r_utils

# Note... If "target_timezone" needs to be UTC, then simply use "UTC".
DEFAULT_TZ = 'US/Eastern'
DEFAULT_FMT = "%Y-%m-%d %H:%M"


def datestr_to_tzdatetime(datestr: str,
                          target_timezone=DEFAULT_TZ) -> datetime:
    """
    Parse virtually any date that is passed in as an argument, in any format. The value of the target_timezone will determine the timezone of the resulting datatime object. If "target_timezone" is omitted, then the datetime object will default to the DEFAULT_TZ timezone. If there is no time within the "date_str", then "00:00" is added.

    Parameters
    ----------
    date_str : str
        Any date as a string, possibly including time.
        Time must be in 24-hour format, e.g. "12:30" or "12:30:00". This is a self-imposed constraint for the sake of simplicity.

    target_timezone : str, optional
        Target timezone of the returned object, by default DEFAULT_TZ. In many cases, the user does not need to be concerned with the timezone.

    Returns
    -------
    datetime
        date_str returned as a timezone-aware datetime object. Time is not changed even if a non-local timezone is included, since the function assumes that if the user passes in a time, that they want the time to be in the target timezone.

    Example
    -------
    dt = "03-19-2023 18:36" from the "US/Eastern" timezone.
    datestr_to_tzdatetime(dt) -->
        datetime(2023, 3, 19, 18, 36, tzinfo=<DstTzInfo 'US/Eastern')

    dt = "03-19-2023 18:36" from the "US/Eastern" timezone.
    datestr_to_tzdatetime(dt, "Asia/Tokyo") -->
        datetime(2023, 3, 19, 18, 36, tzinfo=<DstTzInfo 'Asia/Tokyo')
    """

    try:
        parsed_datetime: datetime = parser.parse(datestr)
    except ParserError as e:
        print(f"Cannot parse a string that is not a date: {datestr}")
        return None

    # Get the target timezone object.
    target_tz = pytz.timezone(target_timezone)

    # Make the datetime object timezone-aware using the localize method.
    if parsed_datetime.tzinfo is None:
        parsed_datetime = target_tz.localize(parsed_datetime)

    return parsed_datetime


def tzdatetime_to_naivedatetime(datetimeobj: datetime) -> datetime:
    """
    Convert a timezone-aware datetime object to a naive datetime object that contains no timezone information.

    Parameters
    ----------
    datetimeobj : datetime
        The datetime object to convert.

    Returns
    -------
    datetime -- naive datetime (no timezone information)

    Example
    -------
    datetime(2023, 3, 19, 18, 36, tzinfo=<DstTzInfo 'US/Eastern') -->

        datetime.datetime(2023, 3, 19, 18, 36)
    """

    datetimestr = datetime_to_datestr(datetimeobj)
    # Convert to timezone-naive datetime object
    naive_datetime = datetime.strptime(datetimestr, "%Y-%m-%d %H:%M")
    # naive_datetime = datetimeobj.replace(tzinfo=None)

    return naive_datetime


def datetime_to_tzdatetime(datetimeobj: datetime, target_timezone=DEFAULT_TZ) -> datetime:
    """
    Convert a naive datetime object to a timezone-aware datetime object.
    """
    target_tz = pytz.timezone(target_timezone)
    return target_tz.localize(datetimeobj)


def datetime_to_datestr(datetimeobj: datetime,
                        target_timezone=DEFAULT_TZ,
                        fmt=DEFAULT_FMT) -> str:
    """
    Convert any datetime to a timezone-adjusted date string with the provided format.

    By "timezone-adjusted", we mean that the time will be offset in the returned string as determined by the target_timezone. If the target_timezone is the same as the timezone of the datetime object passed in, a string will be returned in which the time is not changed.

    Parameters
    ----------
    datetimeobj : datetime
        datetime object that optionally includes timezone information

    target_timezone : str
        Timezone for the target date string; default is DEFAULT_TZ. If the timezone is different from the timezone of the provided datetime object, then the time of the date string will be ajdusted accordingly.

    fmt : str
        Format for the returned string; default is DEFAULT_FMT

    Returns
    -------
    str -- date, as a string with the requested format, potentially with a time offset depending on the value of "target_timezone".

    Example
    -------
    Given a datetime object in the "US/Eastern" timezone, return a date string in the "US/Central" timezone, with a format of "%m-%d-%Y %I%M %p".

    datetime_to_datestr(datetimeobj,
            target_timezone="US/Central",
            fmt="%m-%d-%Y %I:%M %p") -->

        datetimeobj = datetime(2023, 3, 19, 18, 36, tzinfo='US/Eastern')
        return '03-19-2023 05:36 PM'
    """

    # Get the target timezone object.
    target_tz = pytz.timezone(target_timezone)

    if datetimeobj.tzinfo is None or datetimeobj.tzinfo.utcoffset(datetimeobj) is None:
        target_datetime = target_tz.localize(datetimeobj)
    else:
        # Convert the datetime object to the target timezone.
        target_datetime: datetime = datetimeobj.astimezone(target_tz)

    localdatestr: str = datetime.strftime(target_datetime, fmt)

    return localdatestr


def change_timezones(src_datetime: datetime,
                     source_timezone=DEFAULT_TZ,
                     target_timezone=DEFAULT_TZ) -> datetime:
    """
    Convert any datetime object to a timezone-aware datetime object. Both a source-timezone and a target-timezone are needed so that the datetime library can compute the time offset accurately.

    Parameters
    ----------
    datetimeobj : datetime
        datetime object, timezone-aware or naive

    source_timezone : str
        Timezone of the source datetime object

    target_timezone : str
        Timezone for the target datetime object

    Returns
    -------
    datetime -- timezone-aware datetime object in the target timezone

    Examples
    --------
    To change a datetime object from the "US/Eastern" timezone to the "US/Central" timezone:

    datetimeobj = datetime(2023, 3, 19, 18, 36, tzinfo=<DstTzInfo 'US/Eastern')

    change_timezones(datetimeobj,
                    source_timezone="US/Eastern",
                    target_timezone="US/Central"
                    )

    returns:
        datetime(2023, 3, 19, 17, 36, tzinfo=<DstTzInfo 'US/Central')
    """

    source_tz = pytz.timezone(source_timezone)

    # Localize the source datetime if it is timezone naive.
    if src_datetime.tzinfo is None or src_datetime.tzinfo.utcoffset(src_datetime) is None:
        # Assume the source timezone is Eastern if not specified
        src_datetime = source_tz.localize(src_datetime)

    # Convert to the target timezone
    target_tz = pytz.timezone(target_timezone)
    target_datetime: datetime = src_datetime.astimezone(target_tz)

    return target_datetime


def datetime_to_ts(datetimeobj: datetime, source_timezone=DEFAULT_TZ) -> float:
    """
    This function converts any timezone-aware datetime object into its corresponding Unix timestamp, which is the number of seconds since the Unix epoch (January 1, 1970, at 00:00:00 UTC).

    Naive datetimes (not associated with any timezone) are localized to "source_timezone" before conversion to a timestamp.

    The timestamp that is returned will always be the UTC timestamp. If, say an Eastern time zone datetime object is converted to a timestamp, the result will be the same integer value for any other timezone. Conversion of the resulting timestamp back to a datetime object requires a timezone.

    Parameters
    ----------
    dateobject : datetime
        Any datetime object. If the datetime object is naive, it will be localized to the source_timezone.

    source_timezone : str, optional
        Timezone of the source datetime object; default is DEFAULT_TZ.

    Returns
    -------
    float -- timestamp representation of the datetime object in UTC.

    Example
    -------
    datetimeobj = datetime(2023, 3, 19, 18, 36, tzinfo=<DstTzInfo 'US/Eastern' EDT-1 day, 20:00:00 DST>)

    datetime_to_ts(datetimeobj) -> 1679265360.0

    """

    if datetimeobj.tzinfo is None or datetimeobj.tzinfo.utcoffset(datetimeobj) is None:

        source_tz = pytz.timezone(source_timezone)

        datetimeobj = source_tz.localize(datetimeobj)

    return datetimeobj.timestamp()


def datestr_to_ts(datestr: str, fmt=DEFAULT_FMT, source_timezone=DEFAULT_TZ) -> float:
    """
    Convert a date string into a timestamp. See documentation for datetime_to_ts() for more details.

    Since date strings contain no timezone information, the date will need to be localized before conversion to a timestamp. This is required because the datetime module needs to take into account the timezone offset from the date string to UTC. For example, if the date string is in the "US/Central" timezone, then the datetime object will be localized to "US/Central" before conversion to a timestamp.

    Parameters
    ----------
    datestr : str
        Any date string, formatted according to "fmt", with default being DEFAULT_FMT.

    fmt : str, optional
        Format of the date passed in, by default DEFAULT_FMT

    source_timezone : str, optional
        Timezone of the source datetime object; default is DEFAULT_TZ

    Returns
    -------
    float -- timestamp representation of the date string

    Example
    -------
    datestr = '2023-03-19 17:36' # US/Central time

    datestr_to_ts(datestr, source_timezone="US/Central") -> 1679265360.0
    """

    # Parse "datestr" into a timezone-aware datetime object in the "source_timezone".
    # This assures that we know the timezone of the date string.
    parsed_datetime: datetime = datestr_to_tzdatetime(datestr, source_timezone)

    # Convert the parsed datetime object to a date string.
    parsed_datestr: str = datetime_to_datestr(parsed_datetime)

    datetimeobj: datetime = datetime.strptime(parsed_datestr, fmt)

    ts: float = datetimeobj.timestamp()

    return ts


def ts_to_datetime(ts: float, target_timezone=DEFAULT_TZ) -> datetime:
    """
    Convert a timestamp to a timezone-aware datetime object, adjusted in time for the "target_timezone".


    Parameters
    ----------
    ts : float -- timestamp

    target_timezone : str, optional
        Name of a timezone; default is DEFAULT_TZ

    Returns
    -------
    datetime -- timezone-aware local datetime object

    Example
    -------
    ts_to_datetime(1679265360.0, target_timezone="US/Central")

    returns:
        datetime(2023, 3, 19, 17, 36, tzinfo=<DstTzInfo 'US/Central' CDT-1 day, 19:00:00 DST>)
    """

    # Convert the timestamp to a UTC datetime object.
    utc_datetime: datetime = datetime.fromtimestamp(ts, tz=pytz.utc)

    # Define the target timezone
    target_tz = pytz.timezone(target_timezone)

    # Convert the UTC datetime object to Eastern timezone
    dt: datetime = utc_datetime.astimezone(target_tz)

    return dt


def ts_to_datestr(ts: float, target_timezone=DEFAULT_TZ, fmt=DEFAULT_FMT) -> str:
    """
    Convert a timestamp to a date string, adjusted in time for the "target_timezone".

    Parameters
    ----------
    ts : float -- timestamp

    target_timezone : str, optional
        Target timezone; default is DEFAULT_TZ

    fmt : str
        Format for the returned string; default is DEFAULT_FMT

    Returns
    -------
    str -- date, as a string in the requested format

    Example
    -------
    ts_to_datestr(1679265360.0, "US/Eastern") --> '2023-03-19 18:36'
    ts_to_datestr(1679265360.0, "US/Central") --> '2023-03-19 17:36'
    """

    # Convert the timestamp to a datetime object in the "target_timezone".
    ts_datetime: datetime = ts_to_datetime(ts, target_timezone)

    # Convert the datetime to a string with the requested format.
    ts_datestr: str = datetime.strftime(ts_datetime, fmt)

    return ts_datestr


def datetime_to_dow(datetimeobj: datetime, length=-1) -> str:
    """
    Convert a datetime object into a day of the week as the full name or a three-letter abbreviation. Default is full name of the day.

    Parameters
    ----------
    datetimeobj: datetime -- datetime object

    length: int --
        3 is abbreviated weekday ("Mon"). Anything else is "Monday".

    Returns
    -------
    str -- day of the week
    """

    if length == 3:
        # To get the three-letter abbreviation.
        weekday_str: str = datetimeobj.strftime("%a")
    else:
        # To get the full name of the day of the week
        weekday_str = datetimeobj.strftime("%A")

    return weekday_str


def datetime_to_month(datetimeobj: datetime, length=-1) -> tuple[int, str]:
    """
    Return a tuple comprising the month number and the month name. The latter is either the full month name or a 3-letter abbreviation if lenght is 3. Default is full month name.

    Parameters
    ----------
    datetimeobj: datetime -- datetime object

    length: int --
        3 is abbreviated month name; anything else is full name

    Returns
    -------
    tuple[int, str] -- month number, name of the month
    """

    if length == 3:
        # To get the three-letter abbreviation.
        dom: int = datetimeobj.month
        month_name: str = list_of_months(3)[dom]
    else:
        # To get the full name of the day of the week
        dom: int = datetimeobj.month
        month_name: str = list_of_months(-1)[dom]

    return dom, month_name


def num_days_in_month(datetimeobj: datetime) -> int:
    """
    Return the number of days in a month for the provided datetime object.
    """

    return calendar.monthrange(datetimeobj.year, datetimeobj.month)[1]


def list_of_months(length=-1) -> list[str]:
    """
    Return a list of all month names as full name or a 3-letter abbreviation. Default is full month name. The first "month" is an empty string so that the index of the list of months is the month number.
    """
    if length == 3:
        lom: list[str] = list(calendar.month_abbr)
    else:
        lom: list[str] = list(calendar.month_name)

    return lom


def list_of_weekdays(length=-1) -> list[str]:
    """
    Return a list of all weekday names as full name or a 3-letter abbreviation. Default is full weekday name.
    """
    if length == 3:
        lwd: list[str] = list(calendar.day_abbr)
    else:
        lwd: list[str] = list(calendar.day_name)

    # Rotate the list to make "Sunday" the first day and return
    lwd.insert(0, lwd.pop())
    return lwd


if __name__ == '__main__':
    # r_utils.print_documentation(__file__, False)

    dt = datetime.today()
    # ic(dt)
    # tz = datetime_to_tzdatetime(dt, "US/Central")
    # ic(tz)

    ic(datetime_to_month(dt, 3))
