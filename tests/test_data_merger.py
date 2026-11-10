"""Tests for data_merger.py, which builds a new plant record when someone
identifies or imports a plant that isn't in the database yet."""

import api.quantitative_plant
import crud
import data_merger


def test_find_or_create_plant_creates_once(app):
    first = data_merger.find_or_create_plant("Pilea peperomioides")
    second = data_merger.find_or_create_plant("Pilea peperomioides")
    assert first.plant_id == second.plant_id
    assert crud.get_care_details_by_plant_id(first.plant_id) is not None


def test_merge_with_trefle_id_no_longer_crashes(app, monkeypatch):
    # data_merger used to import get_trefle_plant_details, which doesn't exist
    # in api/quantitative_plant.py, so any call with a trefle_id crashed.
    monkeypatch.setattr(api.quantitative_plant, "get_plant_details",
                        lambda pid: {"data": {"id": pid}})
    monkeypatch.setattr(api.quantitative_plant, "get_growth_data",
                        lambda pid: {"data": {"growth": {"light": 8}}})
    plant_data, care_data = data_merger.merge_plant_data("Ficus lyrata", trefle_id=5)
    assert "trefle" in plant_data["data_sources"]
    assert isinstance(care_data, dict)
