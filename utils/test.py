import unittest

from utils.xh import check_valid_square_brackets
from utils.age import plural_age, MODE_DAYS, MODE_MONTHES, MODE_YEARS


class CheckValidatorCase(unittest.TestCase):
    def test_check_valid_square_brackets(self):
        self.assertEqual(check_valid_square_brackets(''), True)
        self.assertEqual(check_valid_square_brackets('[]'), True)
        self.assertEqual(check_valid_square_brackets('[][]'), True)
        self.assertEqual(check_valid_square_brackets('[[][]]'), True)

        self.assertEqual(check_valid_square_brackets('[]['), False)
        self.assertEqual(check_valid_square_brackets(']'), False)
        self.assertEqual(check_valid_square_brackets('['), False)
        self.assertEqual(check_valid_square_brackets('[['), False)
        self.assertEqual(check_valid_square_brackets(']]'), False)


class PluralCase(unittest.TestCase):
    def test_plural_days(self):
        self.assertEqual(plural_age(0, mode=MODE_DAYS), '0 дней')
        self.assertEqual(plural_age(1, mode=MODE_DAYS), '1 день')
        self.assertEqual(plural_age(2, mode=MODE_DAYS), '2 дня')
        self.assertEqual(plural_age(5, mode=MODE_DAYS), '5 дней')
        self.assertEqual(plural_age(11, mode=MODE_DAYS), '11 дней')
        self.assertEqual(plural_age(15, mode=MODE_DAYS), '15 дней')
        self.assertEqual(plural_age(20, mode=MODE_DAYS), '20 дней')
        self.assertEqual(plural_age(21, mode=MODE_DAYS), '21 день')
        self.assertEqual(plural_age(100, mode=MODE_DAYS), '100 дней')
        self.assertEqual(plural_age(101, mode=MODE_DAYS), '101 день')
        self.assertEqual(plural_age(111, mode=MODE_DAYS), '111 дней')

    def test_plural_monthes(self):
        self.assertEqual(plural_age(0, mode=MODE_MONTHES), '0 месяцев')
        self.assertEqual(plural_age(1, mode=MODE_MONTHES), '1 месяц')
        self.assertEqual(plural_age(2, mode=MODE_MONTHES), '2 месяца')
        self.assertEqual(plural_age(5, mode=MODE_MONTHES), '5 месяцев')
        self.assertEqual(plural_age(11, mode=MODE_MONTHES), '11 месяцев')
        self.assertEqual(plural_age(15, mode=MODE_MONTHES), '15 месяцев')
        self.assertEqual(plural_age(20, mode=MODE_MONTHES), '20 месяцев')
        self.assertEqual(plural_age(21, mode=MODE_MONTHES), '21 месяц')
        self.assertEqual(plural_age(100, mode=MODE_MONTHES), '100 месяцев')
        self.assertEqual(plural_age(101, mode=MODE_MONTHES), '101 месяц')
        self.assertEqual(plural_age(111, mode=MODE_MONTHES), '111 месяцев')

    def test_plural_years(self):
        self.assertEqual(plural_age(0, mode=MODE_YEARS), '0 лет')
        self.assertEqual(plural_age(1, mode=MODE_YEARS), '1 год')
        self.assertEqual(plural_age(2, mode=MODE_YEARS), '2 года')
        self.assertEqual(plural_age(5, mode=MODE_YEARS), '5 лет')
        self.assertEqual(plural_age(11, mode=MODE_YEARS), '11 лет')
        self.assertEqual(plural_age(15, mode=MODE_YEARS), '15 лет')
        self.assertEqual(plural_age(20, mode=MODE_YEARS), '20 лет')
        self.assertEqual(plural_age(21, mode=MODE_YEARS), '21 год')
        self.assertEqual(plural_age(100, mode=MODE_YEARS), '100 лет')
        self.assertEqual(plural_age(101, mode=MODE_YEARS), '101 год')
        self.assertEqual(plural_age(111, mode=MODE_YEARS), '111 лет')


if __name__ == '__main__':
    unittest.main()
