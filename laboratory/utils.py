from datetime import datetime, time

from django.utils import timezone
from django.utils.timezone import pytz
from laboratory.settings import TIME_ZONE



def localtime(d: datetime):
    if not d:
        return None
    return timezone.localtime(d)


def strfdatetime(d, format: str):
    if not d:
        return ""
    try:
        return timezone.localtime(d).strftime(format)
    except:
        d = datetime(year=d.year,
                     month=d.month,
                     day=d.day)
        return d.strftime(format)


def strdate(d, short_year=False):
    return strfdatetime(d, '%d.%m.%' + {True: "y", False: "Y"}[short_year])


def strdateiso(d):
    return strfdatetime(d, '%Y.%m.%d')


def strtime(d):
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


def calculate_age(born, year_patient):
    return year_patient.year - born.year - ((year_patient.month, year_patient.day) < (born.month, born.day))


def start_end_year(current_year):
    # возвращает даты-время(начало конец в году): 01.01.ГОД 00:00:00 00:00:01 И 31.12.ГОД 23:59:59 59:59:59
    user_timezone = pytz.timezone(TIME_ZONE)
    d1 = datetime.strptime(f'01.01.{current_year}', '%d.%m.%Y')
    d2 = datetime.strptime(f'31.12.{current_year}', '%d.%m.%Y')
    start_date = datetime.combine(d1, time.min).astimezone(user_timezone)
    end_date = datetime.combine(d2, time.max).astimezone(user_timezone)

    return start_date, end_date
