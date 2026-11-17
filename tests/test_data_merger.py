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
                        lambda pid: {"data": {"id": pid, "common_name": "Fiddle-leaf fig"}})
    monkeypatch.setattr(api.quantitative_plant, "get_growth_data",
                        lambda pid, plant_details=None: {"light": 8, "growth_rate": "Moderate"})
    plant_data, care_data = data_merger.merge_plant_data("Ficus lyrata", trefle_id=5)
    assert "trefle" in plant_data["data_sources"]
    assert plant_data["common_name"] == "Fiddle-leaf fig"
    assert care_data["sunlight_requirements"] == ["Full sun"]
    assert care_data["difficulty_level"] == "Intermediate"


def test_find_or_create_with_trefle_saves_care_details(app, monkeypatch):
    monkeypatch.setattr(api.quantitative_plant, "get_plant_details",
                        lambda pid: {"data": {"id": pid}})
    monkeypatch.setattr(api.quantitative_plant, "get_growth_data",
                        lambda pid, plant_details=None: {"light": 2, "ph_minimum": 5.0,
                                                         "ph_maximum": 6.5})
    plant = data_merger.find_or_create_plant("Ficus lyrata", trefle_id=5)
    details = crud.get_care_details_by_plant_id(plant.plant_id)
    assert details.sunlight_requirements == ["Shade"]
    assert details.soil_preferences.startswith("Acidic")
