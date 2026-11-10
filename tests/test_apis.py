"""Tests for the plant API helpers in api/.

These never call the real APIs: `requests` is swapped for a fake so the
tests run offline, cost no API credits, and check how the code behaves when
an API is down or a key is missing.

To check your real keys against the live APIs, run:
    RUN_LIVE_API_TESTS=1 pytest tests/test_apis.py -k live
"""

import os

import pytest
import requests

import api.perenual as perenual
import api.quantitative_plant as trefle
import api.plant_health as plant_health


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} error")

    def json(self):
        return self.payload


def test_perenual_returns_data_and_sends_timeout(monkeypatch):
    seen = {}

    def fake_get(url, **kwargs):
        seen.update(kwargs, url=url)
        return FakeResponse({"data": [{"id": 1}]})

    monkeypatch.setattr(perenual.requests, "get", fake_get)
    assert perenual.get_plant_list() == {"data": [{"id": 1}]}
    assert seen["timeout"] == perenual.REQUEST_TIMEOUT


def test_perenual_handles_api_down(monkeypatch):
    def boom(url, **kwargs):
        raise requests.exceptions.ConnectionError("down")

    monkeypatch.setattr(perenual.requests, "get", boom)
    assert perenual.get_plant_list() == {"data": []}
    assert perenual.search_plants("rose") == {"data": []}
    assert perenual.get_plant_details(1) == {}


def test_perenual_care_guide_no_longer_crashes(monkeypatch):
    # Used to raise NameError: name 'headers' is not defined
    monkeypatch.setattr(perenual.requests, "get",
                        lambda url, **kw: FakeResponse({}, status=404))
    assert perenual.get_care_guide(1) == {"data": []}


def test_perenual_map_plant_to_model():
    mapped = perenual.map_plant_to_model({"scientific_name": ["Abies alba"], "common_name": "Fir"})
    assert mapped["common_name"] == "Fir"


def test_trefle_without_key_returns_error(monkeypatch):
    monkeypatch.setattr(trefle, "TREFLE_API_KEY", None)
    assert "error" in trefle.get_plant_list()
    assert "error" in trefle.search_plants("rose")


def test_trefle_with_key(monkeypatch):
    monkeypatch.setattr(trefle, "TREFLE_API_KEY", "fake-key")
    monkeypatch.setattr(trefle.requests, "get",
                        lambda url, **kw: FakeResponse({"data": [{"id": 9}]}))
    assert trefle.search_plants("rose") == {"data": [{"id": 9}]}


def test_trefle_growth_mapping_handles_empty_data():
    assert isinstance(trefle.map_growth_data_to_model({}), dict)


def test_plant_health_without_key(monkeypatch, tmp_path):
    monkeypatch.setattr(plant_health, "PLANT_ID_API_KEY", None)
    image = tmp_path / "leaf.jpg"
    image.write_bytes(b"img")
    assert "error" in plant_health.assess_health(str(image))


# ---------- optional live checks (skipped unless you ask for them) ----------

live = pytest.mark.skipif(os.environ.get("RUN_LIVE_API_TESTS") != "1",
                          reason="set RUN_LIVE_API_TESTS=1 to call the real APIs")


@live
def test_live_perenual():
    from dotenv import dotenv_values
    key = dotenv_values().get("PERENUAL_API_KEY")
    if not key:
        pytest.skip("PERENUAL_API_KEY is not in .env")
    response = requests.get("https://perenual.com/api/v2/species-list",
                            params={"key": key, "page": 1, "size": 1}, timeout=10)
    assert response.status_code == 200
