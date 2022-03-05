import functools
from datetime import datetime, time
from typing import Union

from django.db import reset_queries, connection
from django.utils import timezone
from django.utils.timezone import pytz

from laboratory.settings import TIME_ZONE


def localtime(d: datetime):
    if not d:
        return None
    return timezone.localtime(d, pytz.timezone(TIME_ZONE))


def replace_tz(d: datetime):
    if not d:
        return None
    return d.replace(tzinfo=pytz.timezone(TIME_ZONE))


def strfdatetime(d, format: str = '%d.%m.%Y %X'):
    if not d:
        return ""
    try:
        return timezone.localtime(d).strftime(format)
    except:
        d = datetime(year=d.year, month=d.month, day=d.day)
        return d.strftime(format)


def strdate(d, short_year=False):
    return strfdatetime(d, '%d.%m.%' + {True: "y", False: "Y"}[short_year])


def strdateiso(d):
    return strfdatetime(d, '%Y.%m.%d')


def strtime(d: Union[datetime, time]):
    if isinstance(d, time):
        return f"{d.hour:02}:{d.minute:02}:{d.second:02}"
    return strfdatetime(d, '%X')


def strdatetime(d, short_year=False):
    return strfdatetime(d, '%d.%m.%' + {True: "y", False: "Y"}[short_year] + ' %X')


def tsdatetime(d):
    return int(timezone.localtime(d).timestamp())


def current_time(only_date=False):
    user_timezone = pytz.timezone(TIME_ZONE)
    if only_date:
        datetime_object = timezone.now().astimezone(user_timezone).date()
    else:
        datetime_object = timezone.now().astimezone(user_timezone)

    return datetime_object


def current_year():
    return strdate(current_time(only_date=True))[-4:]


def start_end_year():
    # возвращает даты-время(начало конец в году): 01.01.ГОД 00:00:00 00:00:01 И 31.12.ГОД 23:59:59 59:59:59
    user_timezone = pytz.timezone(TIME_ZONE)
    year_today = current_year()
    d1 = datetime.strptime(f'01.01.{year_today}', '%d.%m.%Y')
    d2 = datetime.strptime(f'31.12.{year_today}', '%d.%m.%Y')
    start_date = datetime.combine(d1, time.min).astimezone(user_timezone)
    end_date = datetime.combine(d2, time.max).astimezone(user_timezone)

    return start_date, end_date


def query_debugger(func):
    import time

    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__}")  # noqa: T001
        print(f"Number of Queries : {end_queries - start_queries}")  # noqa: T001
        print(f"Finished in : {(end - start):.2f}s")  # noqa: T001
        return result

    return inner_func
