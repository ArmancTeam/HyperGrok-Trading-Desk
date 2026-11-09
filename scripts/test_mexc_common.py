import json
import unittest
from unittest.mock import patch

from mexc_common import (
    MexcPublicError,
    public_get,
    require_list,
    require_object,
    validate_symbol,
)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return json.dumps({"symbol": "BTCUSDT"}).encode()


class MexcCommonTests(unittest.TestCase):

    def test_spot_symbol(self):
        self.assertEqual(validate_symbol("btcusdt"), "BTCUSDT")

    def test_futures_symbol(self):
        self.assertEqual(
            validate_symbol("btc_usdt", futures=True), "BTC_USDT"
        )

    def test_invalid_symbols(self):
        for symbol in ("", "BTC/USDT", "BTC USDT", "https://bad.com"):
            with self.subTest(symbol=symbol):
                with self.assertRaises(MexcPublicError):
                    validate_symbol(symbol)

    def test_invalid_futures_symbol(self):
        with self.assertRaises(MexcPublicError):
            validate_symbol("BTCUSDT", futures=True)

    @patch("mexc_common.urllib.request.urlopen")
    def test_public_get_uses_fixed_https_host_and_get(self, mocked):
        mocked.return_value = FakeResponse()
        result = public_get("/api/v3/ticker/24hr", {"symbol": "BTCUSDT"})
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.mexc.com/api/v3/ticker/24hr?symbol=BTCUSDT")
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(result["symbol"], "BTCUSDT")

    def test_rejects_unsafe_path(self):
        for path in ("https://evil.example", "//evil.example", "/../private"):
            with self.subTest(path=path):
                with self.assertRaises(MexcPublicError):
                    public_get(path)

    def test_rejects_invalid_timeout(self):
        with self.assertRaises(MexcPublicError):
            public_get("/api/v3/ping", timeout=99)

    def test_response_validators(self):
        self.assertEqual(require_object({"a": 1})["a"], 1)
        self.assertEqual(require_list([1, 2]), [1, 2])
        with self.assertRaises(MexcPublicError):
            require_object([])
        with self.assertRaises(MexcPublicError):
            require_list({})


if __name__ == "__main__":
    unittest.main()
