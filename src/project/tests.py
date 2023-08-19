from django.test import SimpleTestCase

from . import calc


class CalcTest(SimpleTestCase):
    def test_sum(self):
        """test sum two numbers"""
        res = calc.sum(1, 2)
        self.assertEqual(res, 3, "My message error")

    def test_subtract_numbers(self):
        """test subtract two numbers"""
        res = calc.sub(1, 3)
        self.assertEqual(res, -2, "this is error")
