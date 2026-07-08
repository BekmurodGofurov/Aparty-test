"""Unit tests for database.operations.delete.favorites."""

import pytest

from database.operations.delete import favorites as ops


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_callable(self, db_session):
        assert callable(ops.delete)
