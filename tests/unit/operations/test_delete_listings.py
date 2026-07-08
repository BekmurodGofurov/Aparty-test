"""Unit tests for database.operations.delete.listings."""

import pytest

from database.operations.delete import listings as ops


class TestDeleteListing:
    @pytest.mark.asyncio
    async def test_delete_listing_callable(self, db_session):
        assert callable(ops.delete_listing)
