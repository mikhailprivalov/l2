from datetime import datetime

from django.utils import timezone


def localtime(d: datetime):
    return timezone.localtime(d)


def strfdatetime(d: [datetime, None], format: str):
    if not d:
        return ""
    return timezone.localtime(d).strftime(format)


def strdate(d: datetime, short_year=False):
    return strfdatetime(d, '%d.%m.%{}'.format({True: "y", False: "Y"}[short_year]))


def strtime(d: datetime):
    return strfdatetime(d, '%X')


def strdatetime(d: datetime, short_year=False):
    return strfdatetime(d, '%d.%m.%{} %X'.format({True: "y", False: "Y"}[short_year]))


def tsdatetime(d: datetime):
    return int(timezone.localtime(d).timestamp())
