"""Unit tests for database.operations.update.notifications."""

import pytest

from database.operations.update import notifications as ops


class TestMarkAllRead:
    @pytest.mark.asyncio
    async def test_mark_all_read_callable(self, db_session):
        assert callable(ops.mark_all_read)

class TestMarkRead:
    @pytest.mark.asyncio
    async def test_mark_read_callable(self, db_session):
        assert callable(ops.mark_read)
