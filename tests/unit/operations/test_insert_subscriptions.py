"""Unit tests for database.operations.insert.subscriptions."""

import pytest

from database.operations.insert import subscriptions as ops


class TestCreate:
    @pytest.mark.asyncio
    async def test_create_callable(self, db_session):
        assert callable(ops.create)
