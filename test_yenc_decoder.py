import unittest
from src.services.yenc_decoder import decode_yenc

class TestYEncDecoder(unittest.TestCase):
    def test_basic_decoding(self):
        test_data = b"""=ybegin line=128 size=12345 name=test.bin\r\nqwrst\r\n=yend\r\n"""
        decoded = decode_yenc(test_data)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded, b"GMHIJ")  # qwrst in yEnc decodes to GMHIJ

    def test_missing_ybegin(self):
        test_data = b"Just some random data"
        decoded = decode_yenc(test_data)
        self.assertIsNone(decoded)

    def test_invalid_data(self):
        test_data = None
        decoded = decode_yenc(test_data)
        self.assertIsNone(decoded)

if __name__ == "__main__":
    unittest.main()
