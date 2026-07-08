"""Unit tests for database.operations.delete.users."""

import pytest

from database.operations.delete import users as ops


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_callable(self, db_session):
        assert callable(ops.delete)
