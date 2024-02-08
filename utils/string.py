def make_one_char_reduction(w: str, add_dot: bool, append_space=False) -> str:
    w = w.strip()
    if not w:
        return ''
    w = w[0]
    if not w.isdigit() and add_dot:
        w += "."
    if append_space:
        w += " "
    return w


def make_short_name_form(family: str, name: str, patronymic: str, add_dots: bool, with_space: bool) -> str:
    return f"{family} {make_one_char_reduction(name, add_dots, with_space)}{make_one_char_reduction(patronymic, add_dots)}".strip()
