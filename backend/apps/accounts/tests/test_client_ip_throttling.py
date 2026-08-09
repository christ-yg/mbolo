from types import SimpleNamespace

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from apps.core.security_logging import get_client_ip

from ..throttles import (
    EmailTwoFactorChallengeThrottle,
    LoginIPThrottle,
    RegistrationIPThrottle,
)


def build_request(
    *,
    remote_addr: str = "172.20.0.5",
    forwarded_ip: str = "",
    data: dict | None = None,
):
    """Construit le minimum requis par les helpers et throttles DRF."""
    return SimpleNamespace(
        META={
            "REMOTE_ADDR": remote_addr,
            "HTTP_X_MBOLO_CLIENT_IP": forwarded_ip,
        },
        data=data or {},
    )


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mbolo-client-ip-throttle-tests",
        }
    }
)
class ClientIPSecurityTests(SimpleTestCase):
    def setUp(self) -> None:
        cache.clear()

    @override_settings(TRUST_MBOLO_CLIENT_IP_HEADER=False)
    def test_private_header_is_ignored_by_default(self) -> None:
        request = build_request(
            remote_addr="172.20.0.5",
            forwarded_ip="203.0.113.25",
        )

        self.assertEqual(get_client_ip(request), "172.20.0.5")

    @override_settings(TRUST_MBOLO_CLIENT_IP_HEADER=True)
    def test_valid_private_header_is_used_behind_edge_proxy(self) -> None:
        request = build_request(
            remote_addr="172.20.0.5",
            forwarded_ip="203.0.113.25",
        )

        self.assertEqual(get_client_ip(request), "203.0.113.25")

    @override_settings(TRUST_MBOLO_CLIENT_IP_HEADER=True)
    def test_invalid_private_header_falls_back_to_remote_addr(self) -> None:
        request = build_request(
            remote_addr="172.20.0.5",
            forwarded_ip="not-an-ip-address",
        )

        self.assertEqual(get_client_ip(request), "172.20.0.5")

    @override_settings(TRUST_MBOLO_CLIENT_IP_HEADER=True)
    def test_login_throttle_uses_the_normalized_client_ip(self) -> None:
        request = build_request(forwarded_ip="198.51.100.40")
        throttle = LoginIPThrottle()

        self.assertEqual(
            throttle.get_identifier(request, object()),
            "198.51.100.40",
        )

    @override_settings(TRUST_MBOLO_CLIENT_IP_HEADER=False)
    def test_registration_is_limited_after_ten_requests(self) -> None:
        request = build_request(remote_addr="198.51.100.41")

        for _ in range(RegistrationIPThrottle.limit):
            self.assertTrue(
                RegistrationIPThrottle().allow_request(request, object())
            )

        self.assertFalse(
            RegistrationIPThrottle().allow_request(request, object())
        )

    def test_two_factor_challenge_is_limited_after_five_attempts(self) -> None:
        request = build_request(
            data={"challenge_token": "signed-test-challenge"}
        )

        for _ in range(EmailTwoFactorChallengeThrottle.limit):
            self.assertTrue(
                EmailTwoFactorChallengeThrottle().allow_request(
                    request,
                    object(),
                )
            )

        self.assertFalse(
            EmailTwoFactorChallengeThrottle().allow_request(
                request,
                object(),
            )
        )
