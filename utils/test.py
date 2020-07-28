import unittest

from utils.xh import check_valid_square_brackets


class CheckValidatorCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(check_valid_square_brackets(''), True)
        self.assertEqual(check_valid_square_brackets('[]'), True)
        self.assertEqual(check_valid_square_brackets('[][]'), True)
        self.assertEqual(check_valid_square_brackets('[[][]]'), True)

        self.assertEqual(check_valid_square_brackets('[]['), False)
        self.assertEqual(check_valid_square_brackets(']'), False)
        self.assertEqual(check_valid_square_brackets('['), False)
        self.assertEqual(check_valid_square_brackets('[['), False)
        self.assertEqual(check_valid_square_brackets(']]'), False)


if __name__ == '__main__':
    unittest.main()
