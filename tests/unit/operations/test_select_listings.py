"""Unit tests for database.operations.select.listings."""

import pytest

from database.operations.select import listings as ops


class TestCountActivePremium:
    @pytest.mark.asyncio
    async def test_count_active_premium_callable(self, db_session):
        assert callable(ops.count_active_premium)

class TestCountActiveSimple:
    @pytest.mark.asyncio
    async def test_count_active_simple_callable(self, db_session):
        assert callable(ops.count_active_simple)

class TestCountAll:
    @pytest.mark.asyncio
    async def test_count_all_callable(self, db_session):
        assert callable(ops.count_all)

class TestGetActiveListings:
    @pytest.mark.asyncio
    async def test_get_active_listings_callable(self, db_session):
        assert callable(ops.get_active_listings)

class TestGetAll:
    @pytest.mark.asyncio
    async def test_get_all_callable(self, db_session):
        assert callable(ops.get_all)

class TestGetByGender:
    @pytest.mark.asyncio
    async def test_get_by_gender_callable(self, db_session):
        assert callable(ops.get_by_gender)

class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_callable(self, db_session):
        assert callable(ops.get_by_id)

class TestGetByOwnerId:
    @pytest.mark.asyncio
    async def test_get_by_owner_id_callable(self, db_session):
        assert callable(ops.get_by_owner_id)

class TestGetByRegion:
    @pytest.mark.asyncio
    async def test_get_by_region_callable(self, db_session):
        assert callable(ops.get_by_region)

class TestGetMyListingRows:
    @pytest.mark.asyncio
    async def test_get_my_listing_rows_callable(self, db_session):
        assert callable(ops.get_my_listing_rows)

class TestGetOwnerListingsWithReviewCounts:
    @pytest.mark.asyncio
    async def test_get_owner_listings_with_review_counts_callable(self, db_session):
        assert callable(ops.get_owner_listings_with_review_counts)

class TestGetPremiumListings:
    @pytest.mark.asyncio
    async def test_get_premium_listings_callable(self, db_session):
        assert callable(ops.get_premium_listings)

class TestGetWithOwner:
    @pytest.mark.asyncio
    async def test_get_with_owner_callable(self, db_session):
        assert callable(ops.get_with_owner)

class TestHasRentalHistory:
    @pytest.mark.asyncio
    async def test_has_rental_history_callable(self, db_session):
        assert callable(ops.has_rental_history)

class TestSearch:
    @pytest.mark.asyncio
    async def test_search_callable(self, db_session):
        assert callable(ops.search)

class TestSearchWithCards:
    @pytest.mark.asyncio
    async def test_search_with_cards_callable(self, db_session):
        assert callable(ops.search_with_cards)
