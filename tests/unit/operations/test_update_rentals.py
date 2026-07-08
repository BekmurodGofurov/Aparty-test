"""Unit tests for database.operations.update.rentals."""

import pytest

from database.operations.update import rentals as ops


class TestAcceptRequest:
    @pytest.mark.asyncio
    async def test_accept_request_callable(self, db_session):
        assert callable(ops.accept_request)

class TestDeactivateRental:
    @pytest.mark.asyncio
    async def test_deactivate_rental_callable(self, db_session):
        assert callable(ops.deactivate_rental)

class TestRejectRequest:
    @pytest.mark.asyncio
    async def test_reject_request_callable(self, db_session):
        assert callable(ops.reject_request)

class TestRejectRequests:
    @pytest.mark.asyncio
    async def test_reject_requests_callable(self, db_session):
        assert callable(ops.reject_requests)
