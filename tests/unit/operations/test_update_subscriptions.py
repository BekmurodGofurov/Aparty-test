"""Unit tests for database.operations.update.subscriptions."""

import pytest

from database.operations.update import subscriptions as ops


class TestDeactivate:
    @pytest.mark.asyncio
    async def test_deactivate_callable(self, db_session):
        assert callable(ops.deactivate)

class TestIncrementUsedCount:
    @pytest.mark.asyncio
    async def test_increment_used_count_callable(self, db_session):
        assert callable(ops.increment_used_count)
