"""Unit tests for database.operations.insert.rentals."""

import pytest

from database.operations.insert import rentals as ops


class TestCreateMaintenanceReport:
    @pytest.mark.asyncio
    async def test_create_maintenance_report_callable(self, db_session):
        assert callable(ops.create_maintenance_report)

class TestCreateNotification:
    @pytest.mark.asyncio
    async def test_create_notification_callable(self, db_session):
        assert callable(ops.create_notification)

class TestCreateRental:
    @pytest.mark.asyncio
    async def test_create_rental_callable(self, db_session):
        assert callable(ops.create_rental)

class TestCreateRentalRequest:
    @pytest.mark.asyncio
    async def test_create_rental_request_callable(self, db_session):
        assert callable(ops.create_rental_request)

class TestCreateRequestMessage:
    @pytest.mark.asyncio
    async def test_create_request_message_callable(self, db_session):
        assert callable(ops.create_request_message)

class TestCreateRoomMessage:
    @pytest.mark.asyncio
    async def test_create_room_message_callable(self, db_session):
        assert callable(ops.create_room_message)
