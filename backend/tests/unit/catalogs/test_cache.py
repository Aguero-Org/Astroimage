from __future__ import annotations

from uuid import uuid4

from astroimage.catalogs.cache import CatalogRecommendationCache, recommendation_cache_key
from astroimage.catalogs.schema import (
    CatalogRecommendationConfigSchema,
    CatalogRecommendationResponse,
)


def test_cache_stores_and_returns_results() -> None:
    cache = CatalogRecommendationCache()
    response = CatalogRecommendationResponse(source_name="survey.fits", queried=True)
    cache.set("key", response)
    assert cache.get("key") is response
    assert cache.get("missing") is None
    cache.clear()
    assert cache.get("key") is None


def test_cache_evicts_oldest_beyond_capacity() -> None:
    cache = CatalogRecommendationCache(max_entries=2)
    cache.set("a", CatalogRecommendationResponse(source_name="a"))
    cache.set("b", CatalogRecommendationResponse(source_name="b"))
    cache.set("c", CatalogRecommendationResponse(source_name="c"))
    assert cache.get("a") is None
    assert cache.get("b") is not None
    assert cache.get("c") is not None


def test_recommendation_cache_key_depends_on_config_and_client() -> None:
    record_id = uuid4()
    base = recommendation_cache_key(
        record_id=record_id,
        client_id="alice",
        hdu_index=None,
        config=CatalogRecommendationConfigSchema(),
    )
    other_client = recommendation_cache_key(
        record_id=record_id,
        client_id="bob",
        hdu_index=None,
        config=CatalogRecommendationConfigSchema(),
    )
    other_config = recommendation_cache_key(
        record_id=record_id,
        client_id="alice",
        hdu_index=None,
        config=CatalogRecommendationConfigSchema(include_papers=False),
    )
    assert base != other_client
    assert base != other_config
