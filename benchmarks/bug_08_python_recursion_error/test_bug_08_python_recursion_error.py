import unittest
from .main import factorial

class TestFactorial(unittest.TestCase):

    def test_factorial_of_0(self):
        self.assertEqual(factorial(0), 1)

    def test_factorial_of_1(self):
        self.assertEqual(factorial(1), 1)

    def test_factorial_of_5(self):
        self.assertEqual(factorial(5), 120)

    def test_factorial_of_10(self):
        self.assertEqual(factorial(10), 3628800)

    def test_factorial_of_11(self):
        # This test will fail because of the bug
        self.assertEqual(factorial(11), 39916800)

    def test_negative_input(self):
        with self.assertRaises(ValueError):
            factorial(-1)

if __name__ == '__main__':
    unittest.main()
