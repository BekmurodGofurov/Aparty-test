"""Unit tests for database.operations.update.reviews."""

import pytest

from database.operations.update import reviews as ops


class TestUpdateFields:
    @pytest.mark.asyncio
    async def test_update_fields_callable(self, db_session):
        assert callable(ops.update_fields)
