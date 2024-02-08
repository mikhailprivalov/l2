MODE_DAYS = 'days'
MODE_MONTHES = 'monthes'
MODE_YEARS = 'years'

MODES = {
    MODE_DAYS: ['день', 'дня', 'дней'],
    MODE_MONTHES: ['месяц', 'месяца', 'месяцев'],
    MODE_YEARS: ['год', 'года', 'лет'],
}

def plural_age(n, mode=MODE_YEARS):    
    if n % 10 == 1 and n % 100 != 11:
        p = 0
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        p = 1
    else:
        p = 2

    return f'{n} {MODES[mode][p]}'
