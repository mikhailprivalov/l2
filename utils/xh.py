import simplejson as json

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


def check_float_is_valid(val):
    try:
        float(val)
        return True
    except ValueError:
        return False
