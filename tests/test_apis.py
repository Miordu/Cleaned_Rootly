"""Tests for the Trefle client in api/quantitative_plant.py.

These never call the real API: `requests` and the clock are swapped for
fakes, so the tests run offline, use none of your 60 requests a minute, and
finish instantly even when they check the waiting logic.

To check your real token against the live API, run:
    RUN_LIVE_API_TESTS=1 pytest tests/test_apis.py -k live
"""

import os

import pytest
import requests

import api.quantitative_plant as trefle


class FakeResponse:
    def __init__(self, payload=None, status=200, headers=None):
        self.payload = payload if payload is not None else {"data": []}
        self.status_code = status
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} error")

    def json(self):
        return self.payload


class FakeClock:
    """Stands in for time.sleep/time.monotonic/time.time so waits are instant."""

    def __init__(self):
        self.now = 1000.0
        self.slept = []

    def sleep(self, seconds):
        self.slept.append(round(seconds, 3))
        self.now += seconds

    def monotonic(self):
        return self.now

    def time(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(trefle.time, "sleep", fake.sleep)
    monkeypatch.setattr(trefle.time, "monotonic", fake.monotonic)
    monkeypatch.setattr(trefle.time, "time", fake.time)
    monkeypatch.setattr(trefle, "_recent_requests", trefle.deque())
    monkeypatch.setattr(trefle, "_blocked_until", 0.0)
    # Wait as long as needed, the way the bulk seed scripts do. (The website
    # sets a short limit; test_website_does_not_hang_on_the_limit covers that.)
    monkeypatch.setattr(trefle, "MAX_BLOCKING_WAIT", None)
    return fake


@pytest.fixture
def with_key(monkeypatch):
    monkeypatch.setenv("TREFLE_API_KEY", "fake-token")


def test_no_key_returns_error_without_calling_trefle(monkeypatch):
    monkeypatch.setenv("TREFLE_API_KEY", "")

    def should_not_run(*a, **kw):
        raise AssertionError("called Trefle without a key")

    monkeypatch.setattr(trefle.requests, "get", should_not_run)
    assert "error" in trefle.get_plant_list()
    assert "error" in trefle.search_plants("rose")
    assert "error" in trefle.get_plant_details(1)


def test_key_is_read_from_env_and_sent_with_timeout(monkeypatch, with_key, clock):
    seen = {}

    def fake_get(url, params=None, timeout=None):
        seen.update(url=url, params=params, timeout=timeout)
        return FakeResponse({"data": [{"id": 9}]})

    monkeypatch.setattr(trefle.requests, "get", fake_get)
    assert trefle.search_plants("rose") == {"data": [{"id": 9}]}
    assert seen["url"].endswith("/plants/search")
    assert seen["params"]["q"] == "rose"
    assert seen["params"]["token"] == "fake-token"
    assert seen["timeout"] == trefle.REQUEST_TIMEOUT


def test_api_down_returns_error_and_hides_key(monkeypatch, with_key, clock, caplog):
    def boom(url, **kw):
        raise requests.exceptions.ConnectionError(f"{url}?token=fake-token failed")

    monkeypatch.setattr(trefle.requests, "get", boom)
    assert "error" in trefle.get_plant_list()
    assert "fake-token" not in caplog.text
    assert "fake-token" not in trefle.get_plant_list()["error"]


def test_website_does_not_hang_on_the_limit(monkeypatch, with_key, clock):
    # With a short MAX_BLOCKING_WAIT (what server.py sets), the 61st request
    # gives up straight away with an error instead of freezing the page
    monkeypatch.setattr(trefle, "MAX_BLOCKING_WAIT", 3)
    sent = []
    monkeypatch.setattr(trefle.requests, "get", lambda url, **kw: sent.append(url) or FakeResponse())
    for _ in range(60):
        trefle.get_plant_list()
    assert "error" in trefle.get_plant_list()
    assert clock.slept == [] and len(sent) == 60


def test_stays_under_60_requests_a_minute(monkeypatch, with_key, clock):
    monkeypatch.setattr(trefle.requests, "get", lambda url, **kw: FakeResponse())
    for _ in range(60):
        trefle.get_plant_list()
    assert clock.slept == []  # the first 60 go straight through

    trefle.get_plant_list()  # the 61st waits for the oldest to be a minute old
    assert clock.slept == [60.0]


def test_requests_spread_out_over_time_do_not_wait(monkeypatch, with_key, clock):
    monkeypatch.setattr(trefle.requests, "get", lambda url, **kw: FakeResponse())
    for _ in range(120):
        trefle.get_plant_list()
        clock.now += 1.0  # one request a second is exactly 60 a minute
    assert clock.slept == []


def test_retries_after_429_using_retry_after(monkeypatch, with_key, clock):
    answers = [FakeResponse(status=429, headers={"Retry-After": "7"}),
               FakeResponse({"data": [{"id": 1}]})]
    monkeypatch.setattr(trefle.requests, "get", lambda url, **kw: answers.pop(0))
    assert trefle.get_plant_list() == {"data": [{"id": 1}]}
    assert clock.slept == [7.0]


def test_gives_up_after_repeated_429(monkeypatch, with_key, clock):
    calls = []

    def always_429(url, **kw):
        calls.append(url)
        return FakeResponse(status=429)

    monkeypatch.setattr(trefle.requests, "get", always_429)
    assert "error" in trefle.get_plant_list()
    assert len(calls) == trefle.MAX_RETRIES + 1
    assert clock.slept == [2.0, 4.0]  # no Retry-After header: wait 2s, then 4s


def test_retry_wait_is_capped(monkeypatch, with_key, clock):
    answers = [FakeResponse(status=429, headers={"Retry-After": "3600"}), FakeResponse()]
    monkeypatch.setattr(trefle.requests, "get", lambda url, **kw: answers.pop(0))
    trefle.get_plant_list()
    assert clock.slept == [trefle.MAX_RETRY_WAIT]


def test_waits_when_trefle_says_quota_is_used_up(monkeypatch, with_key, clock):
    # Another program sharing the key used up this minute's quota
    first = FakeResponse(headers={"RateLimit-Remaining": "0",
                                  "RateLimit-Reset": str(clock.now + 12)})
    answers = [first, FakeResponse()]
    monkeypatch.setattr(trefle.requests, "get", lambda url, **kw: answers.pop(0))
    trefle.get_plant_list()
    assert clock.slept == []  # the answer we already have comes back right away
    trefle.get_plant_list()
    assert clock.slept == [12.0]  # the next request waits for the reset


def test_growth_data_reuses_details_and_reads_trefle_fields(monkeypatch):
    def should_not_run(pid):
        raise AssertionError("fetched details twice")

    monkeypatch.setattr(trefle, "get_plant_details", should_not_run)
    details = {"data": {"main_species": {
        "specifications": {"growth_rate": "Rapid", "average_height": {"cm": 120}},
        "growth": {"light": 5, "bloom_months": ["may", "jun"],
                   "minimum_temperature": {"deg_c": 5}, "maximum_temperature": {"deg_c": 30},
                   "ph_minimum": 6.0, "ph_maximum": 7.0},
    }}}
    growth = trefle.get_growth_data(1, plant_details=details)
    assert growth["average_height_cm"] == 120
    assert growth["temperature_minimum_deg_c"] == 5

    care = trefle.map_growth_data_to_model(growth)
    assert care["sunlight_requirements"] == ["Partial sun"]
    assert care["temperature_range"] == "5°C to 30°C"
    assert care["difficulty_level"] == "Easy"
    assert care["pruning_months"] == ["may", "jun"]
    assert care["soil_preferences"].startswith("Neutral")


def test_growth_data_handles_missing_sections():
    growth = trefle.get_growth_data(1, plant_details={"data": {"main_species": None}})
    assert growth["light"] is None
    assert trefle.map_growth_data_to_model(growth)["sunlight_requirements"] == []
    assert trefle.map_growth_data_to_model({"error": "x"}) == {}


def test_map_plant_to_model():
    mapped = trefle.map_plant_to_model({"scientific_name": "Abies alba",
                                        "common_name": "Silver fir", "family": "Pinaceae"})
    assert mapped["common_name"] == "Silver fir"
    assert mapped["description"] == "A plant in the Pinaceae family."
    assert mapped["data_sources"] == ["trefle"]


# ---------- optional live check (skipped unless you ask for it) ----------

@pytest.mark.skipif(os.environ.get("RUN_LIVE_API_TESTS") != "1",
                    reason="set RUN_LIVE_API_TESTS=1 to call the real Trefle API")
def test_live_trefle(monkeypatch):
    from dotenv import dotenv_values
    key = dotenv_values().get("TREFLE_API_KEY")
    if not key:
        pytest.skip("TREFLE_API_KEY is not in .env")
    monkeypatch.setenv("TREFLE_API_KEY", key)
    result = trefle.search_plants("monstera")
    assert "error" not in result, result["error"]
    assert result["data"], "Trefle returned no plants for 'monstera'"
