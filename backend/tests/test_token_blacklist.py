"""Testes do armazenamento de revogacao e refresh tokens."""

import time

from security.token_blacklist import TokenBlacklist


def make_unavailable_blacklist() -> TokenBlacklist:
    blacklist = TokenBlacklist.__new__(TokenBlacklist)
    blacklist.redis_client = None
    blacklist.is_available = False
    blacklist._warning_logged = False
    blacklist._memory_blacklist = {}
    blacklist._memory_refresh_tokens = {}
    blacklist._last_connection_attempt = time.time()
    blacklist._retry_interval_seconds = 30
    return blacklist


def test_unknown_refresh_token_fails_closed_without_redis():
    blacklist = make_unavailable_blacklist()

    assert blacklist.is_refresh_token_valid("unknown-token", 42) is False


def test_known_refresh_token_works_in_memory_fallback():
    blacklist = make_unavailable_blacklist()

    assert blacklist.add_refresh_token("known-token", 42, expires_in=60) is True
    assert blacklist.is_refresh_token_valid("known-token", 42) is True

    blacklist.revoke_refresh_token("known-token", 42)
    assert blacklist.is_refresh_token_valid("known-token", 42) is False


def test_blacklisted_access_token_survives_redis_failure():
    blacklist = make_unavailable_blacklist()

    assert blacklist.add_to_blacklist("access-token", expires_in=60) is True
    assert blacklist.is_blacklisted("access-token") is True
