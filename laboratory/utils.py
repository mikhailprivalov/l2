from datetime import datetime, date

from django.utils import timezone


def localtime(d: datetime):
    return timezone.localtime(d)


def strfdatetime(d: [datetime, None, date], format: str):
    if not d:
        return ""
    if isinstance(d, date):
        d = datetime(year=d.year,
                     month=d.month,
                     day=d.day)
        return d.strftime(format)
    return timezone.localtime(d).strftime(format)


def strdate(d: datetime, short_year=False):
    return strfdatetime(d, '%d.%m.%{}'.format({True: "y", False: "Y"}[short_year]))


def strtime(d: datetime):
    return strfdatetime(d, '%X')


def strdatetime(d: datetime, short_year=False):
    return strfdatetime(d, '%d.%m.%{} %X'.format({True: "y", False: "Y"}[short_year]))


def tsdatetime(d: datetime):
    return int(timezone.localtime(d).timestamp())
