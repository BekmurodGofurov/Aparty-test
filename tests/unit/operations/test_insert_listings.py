"""Unit tests for database.operations.insert.listings."""

import pytest

from database.operations.insert import listings as ops


class TestCommitListing:
    @pytest.mark.asyncio
    async def test_commit_listing_callable(self, db_session):
        assert callable(ops.commit_listing)

class TestCreateListing:
    @pytest.mark.asyncio
    async def test_create_listing_callable(self, db_session):
        assert callable(ops.create_listing)

class TestCreateListingPayment:
    @pytest.mark.asyncio
    async def test_create_listing_payment_callable(self, db_session):
        assert callable(ops.create_listing_payment)
