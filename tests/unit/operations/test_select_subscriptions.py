"""Unit tests for database.operations.select.subscriptions."""

import pytest

from database.operations.select import subscriptions as ops


class TestGetActiveSubscription:
    @pytest.mark.asyncio
    async def test_get_active_subscription_callable(self, db_session):
        assert callable(ops.get_active_subscription)

class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_callable(self, db_session):
        assert callable(ops.get_by_id)

class TestGetByType:
    @pytest.mark.asyncio
    async def test_get_by_type_callable(self, db_session):
        assert callable(ops.get_by_type)

class TestGetByUserId:
    @pytest.mark.asyncio
    async def test_get_by_user_id_callable(self, db_session):
        assert callable(ops.get_by_user_id)

class TestGetMySubscriptions:
    @pytest.mark.asyncio
    async def test_get_my_subscriptions_callable(self, db_session):
        assert callable(ops.get_my_subscriptions)

class TestHasAvailableListings:
    @pytest.mark.asyncio
    async def test_has_available_listings_callable(self, db_session):
        assert callable(ops.has_available_listings)
