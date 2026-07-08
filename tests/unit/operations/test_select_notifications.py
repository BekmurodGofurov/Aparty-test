"""Unit tests for database.operations.select.notifications."""

import pytest

from database.operations.select import notifications as ops


class TestCountUnread:
    @pytest.mark.asyncio
    async def test_count_unread_callable(self, db_session):
        assert callable(ops.count_unread)

class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_callable(self, db_session):
        assert callable(ops.get_by_id)

class TestGetMyNotifications:
    @pytest.mark.asyncio
    async def test_get_my_notifications_callable(self, db_session):
        assert callable(ops.get_my_notifications)
