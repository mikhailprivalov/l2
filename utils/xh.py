def fix(s: str):
    return s.replace('<br>', '<br/>')


def check_valid_square_brackets(v: str):
    count = 0
    weights = {'[': -1, ']': 1}
    for s in v:
        if s in weights:
            count += weights[s]
            if count > 0:
                return False
    if count < 0:
        return False

    return True
