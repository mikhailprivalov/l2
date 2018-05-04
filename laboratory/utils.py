from datetime import datetime

from django.utils import timezone


def localtime(d: datetime):
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


def strtime(d):
    return strfdatetime(d, '%X')


def strdatetime(d, short_year=False):
    return strfdatetime(d, '%d.%m.%' + {True: "y", False: "Y"}[short_year] + ' %X')


def tsdatetime(d):
    return int(timezone.localtime(d).timestamp())
