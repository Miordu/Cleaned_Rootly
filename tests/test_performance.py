"""Rough speed checks, so a slow query gets noticed. Limits are generous."""

import time

import api.perenual
import crud


def test_search_is_fast(app):
    for i in range(50):
        crud.create_plant(scientific_name=f"Performance Plant {i}", common_name=f"Test Plant {i}")
    start = time.perf_counter()
    results = crud.search_plants("Performance")
    assert len(results) == 50
    assert time.perf_counter() - start < 0.5


def test_browse_page_is_fast(client, monkeypatch):
    # The old test asked for /plants, which doesn't exist; the page is /browse-plants
    monkeypatch.setattr(api.perenual, "get_plant_list", lambda page=1, **kw: {"data": []})
    for i in range(20):
        crud.create_plant(scientific_name=f"Plant {i}")
    start = time.perf_counter()
    response = client.get("/browse-plants")
    assert response.status_code == 200
    assert time.perf_counter() - start < 1.0
