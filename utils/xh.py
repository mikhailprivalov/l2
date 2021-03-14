from podrazdeleniya.models import Podrazdeleniya


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


def get_hospitals_podrazdeleniya(hospital):
    podrazdeleniya = Podrazdeleniya.objects.values('pk', 'short_title', 'title').filter(p_type=7, hide=False, hospital_id=hospital).order_by('title')
    return [{"id": x["pk"], "label": x['short_title'] or x['title']} for x in podrazdeleniya]


def short_fio_dots(fio):
    fio_list = fio.split(' ')
    f = fio_list[0]
    n = fio_list[1][0:1] + '.'
    p = fio_list[2][0:1] + '.' if len(fio_list) > 2 else ''
    npf = n + ' ' + p + ' ' + f

    return npf
