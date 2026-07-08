"""Unit tests for database.operations.delete.subscriptions."""

import pytest

from database.operations.delete import subscriptions as ops


class TestDeleteById:
    @pytest.mark.asyncio
    async def test_delete_by_id_callable(self, db_session):
        assert callable(ops.delete_by_id)
