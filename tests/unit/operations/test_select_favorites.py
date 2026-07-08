"""Unit tests for database.operations.select.favorites."""

import pytest

from database.operations.select import favorites as ops


class TestGetByUserAndListing:
    @pytest.mark.asyncio
    async def test_get_by_user_and_listing_callable(self, db_session):
        assert callable(ops.get_by_user_and_listing)

class TestGetMyFavoritesRows:
    @pytest.mark.asyncio
    async def test_get_my_favorites_rows_callable(self, db_session):
        assert callable(ops.get_my_favorites_rows)
