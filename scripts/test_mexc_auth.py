import hashlib
import hmac
import json
import unittest
from unittest.mock import patch

from mexc_auth import (
    MexcAuthError,
    signed_spot_get,
    signed_futures_get,
)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return json.dumps({"success": True}).encode()


class MexcAuthTests(unittest.TestCase):

    @patch("mexc_auth.urllib.request.urlopen")
    def test_spot_signature_and_get(self, mocked):
        mocked.return_value = FakeResponse()

        result = signed_spot_get(
            "/api/v3/account",
            {},
            "test-key",
            "test-secret",
            timestamp_ms=123456,
        )

        request = mocked.call_args.args[0]
        query = "timestamp=123456"
        expected = hmac.new(
            b"test-secret",
            query.encode(),
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(result["success"], True)
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("signature=" + expected, request.full_url)
        self.assertEqual(
            request.get_header("X-mexc-apikey"),
            "test-key",
        )

    @patch("mexc_auth.urllib.request.urlopen")
    def test_futures_signature_and_get(self, mocked):
        mocked.return_value = FakeResponse()

        signed_futures_get(
            "/api/v1/private/account/asset/USDT",
            {},
            "test-key",
            "test-secret",
            timestamp_ms=123456,
        )

        request = mocked.call_args.args[0]
        expected = hmac.new(
            b"test-secret",
            b"test-key123456",
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            request.get_header("Apikey"),
            "test-key",
        )
        self.assertEqual(
            request.get_header("Request-time"),
            "123456",
        )
        self.assertEqual(
            request.get_header("Signature"),
            expected,
        )

    def test_missing_credentials_rejected(self):
        with self.assertRaises(MexcAuthError):
            signed_spot_get(
                "/api/v3/account", {}, "", "secret"
            )

        with self.assertRaises(MexcAuthError):
            signed_futures_get(
                "/api/v1/private/account/asset/USDT",
                {}, "key", ""
            )

    def test_unsafe_path_rejected(self):
        with self.assertRaises(MexcAuthError):
            signed_spot_get(
                "/../private", {}, "key", "secret"
            )

    def test_reserved_spot_parameters_rejected(self):
        with self.assertRaises(MexcAuthError):
            signed_spot_get(
                "/api/v3/account",
                {"signature": "fake"},
                "key",
                "secret",
            )


if __name__ == "__main__":
    unittest.main()
