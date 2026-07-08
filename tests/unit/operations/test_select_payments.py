"""Unit tests for database.operations.select.payments."""

import pytest

from database.operations.select import payments as ops


class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_callable(self, db_session):
        assert callable(ops.get_by_id)

class TestGetByPayerId:
    @pytest.mark.asyncio
    async def test_get_by_payer_id_callable(self, db_session):
        assert callable(ops.get_by_payer_id)

class TestGetByRentalAndMonth:
    @pytest.mark.asyncio
    async def test_get_by_rental_and_month_callable(self, db_session):
        assert callable(ops.get_by_rental_and_month)

class TestGetByRentalId:
    @pytest.mark.asyncio
    async def test_get_by_rental_id_callable(self, db_session):
        assert callable(ops.get_by_rental_id)

class TestGetByStatus:
    @pytest.mark.asyncio
    async def test_get_by_status_callable(self, db_session):
        assert callable(ops.get_by_status)

class TestGetOverduePayments:
    @pytest.mark.asyncio
    async def test_get_overdue_payments_callable(self, db_session):
        assert callable(ops.get_overdue_payments)

class TestGetPendingPayments:
    @pytest.mark.asyncio
    async def test_get_pending_payments_callable(self, db_session):
        assert callable(ops.get_pending_payments)

class TestListByPayer:
    @pytest.mark.asyncio
    async def test_list_by_payer_callable(self, db_session):
        assert callable(ops.list_by_payer)

class TestSumTotalRevenue:
    @pytest.mark.asyncio
    async def test_sum_total_revenue_callable(self, db_session):
        assert callable(ops.sum_total_revenue)
