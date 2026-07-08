"""Unit tests for database.operations.update.payments."""

import pytest

from database.operations.update import payments as ops


class TestMarkAsOverdue:
    @pytest.mark.asyncio
    async def test_mark_as_overdue_callable(self, db_session):
        assert callable(ops.mark_as_overdue)

class TestMarkAsPaid:
    @pytest.mark.asyncio
    async def test_mark_as_paid_callable(self, db_session):
        assert callable(ops.mark_as_paid)

class TestUpdateFields:
    @pytest.mark.asyncio
    async def test_update_fields_callable(self, db_session):
        assert callable(ops.update_fields)

class TestUpdateStatus:
    @pytest.mark.asyncio
    async def test_update_status_callable(self, db_session):
        assert callable(ops.update_status)
