from datetime import datetime, timedelta
from typing import Union
from django.utils import timezone


def try_strptime(s, formats=('%d.%m.%Y',), delta: timedelta = None) -> Union[datetime, None]:
    for fmt in formats:
        try:
            r = datetime.strptime(s, fmt)
            if delta:
                r += delta
            return r
        except:
            continue
    return None


def try_parse_range(f, t=None, formats=('%d.%m.%Y',)):
    pf = try_strptime(f, formats)
    pt = try_strptime(t or f, formats, timedelta(1))
    ok = bool(pf and pt)
    if not ok:
        pf = pt = timezone.now() + timedelta(730)
    return pf, pt


def now():
    return timezone.now()


def normalize_date(date_value: str):
    if date_value:
        vv = date_value.split('-')
        if len(vv) == 3:
            date_value = "{}.{}.{}".format(vv[2], vv[1], vv[0])
    return date_value


def normalize_dots_date(s):
    if '.' in s:
        s = s.split('.')
        s = '{}-{}-{}'.format(s[2], s[1], s[0])
    return s


def normalize_dash_date(s):
    if '-' in s:
        s = s.split('-')
        s = '{}.{}.{}'.format(s[2], s[1], s[0])
    return s


def valid_date(s):
    try:
        datetime.strptime(s, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False


def date_iter_range(start_date, end_date, more_1=False, step=1):
    for n in range(0, int((end_date - start_date).days) + (1 if more_1 else 0), step):
        yield start_date + timedelta(n)
