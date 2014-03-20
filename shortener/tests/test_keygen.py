from twisted.trial.unittest import TestCase
from shortener.keygen import generate_token


class TestKeygen(TestCase):
    timeout = 1

    def test_tokens_generated(self):
        self.assertEqual(generate_token(0), 'q70')
        self.assertEqual(generate_token(1), 'qr0')
        self.assertEqual(generate_token(10), 'qP0')
        self.assertEqual(generate_token(4000), '00x')
        self.assertEqual(generate_token(77), 'qYR')
        self.assertEqual(generate_token(65), 'qeR')
        self.assertEqual(generate_token(45), 'q6R')

    def test_invalid_counter(self):
        self.assertRaises(TypeError, generate_token, 1.4)

    def test_custom_alphabet(self):
        alphabet = '0123456789'
        self.assertEqual(generate_token(45, alphabet), '5529')
        self.assertEqual(generate_token(7, alphabet), '5979')
        self.assertEqual(generate_token(4000, alphabet), '1999')
        self.assertEqual(generate_token(77, alphabet), '5779')
