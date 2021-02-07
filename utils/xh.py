from podrazdeleniya.models import Podrazdeleniya
from hospitals.models import Hospitals


def fix(s: str):
    return s.replace('<br>', '<br/>')


SQUARE_BRACKETS_WEIGHTS = {'[': -1, ']': 1}


def check_valid_square_brackets(v: str):
    count = 0
    for s in v:
        if s in SQUARE_BRACKETS_WEIGHTS:
            count += SQUARE_BRACKETS_WEIGHTS[s]
            if count > 0:
                return False
    return count == 0


def check_number_is_valid(s):
    s = str(s)
    if s.isdigit():
        return True
    return check_float_is_valid(s)


def check_float_is_valid(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


def get_hospitals_podrazdeleniya(hospital_pk):
    podrazdeleniya = Podrazdeleniya.objects.values('pk', 'short_title', 'title').filter(p_type=7, hide=False, hospital=hospital_pk).order_by('title')
    return [{"id": x.pk, "label": x['short_title'] or x['title']} for x in podrazdeleniya]
