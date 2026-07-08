"""Unit tests for database.operations.select.rentals."""

import pytest

from database.operations.select import rentals as ops


class TestCountActiveByStudent:
    @pytest.mark.asyncio
    async def test_count_active_by_student_callable(self, db_session):
        assert callable(ops.count_active_by_student)

class TestCountPendingByRequester:
    @pytest.mark.asyncio
    async def test_count_pending_by_requester_callable(self, db_session):
        assert callable(ops.count_pending_by_requester)

class TestCountRoommates:
    @pytest.mark.asyncio
    async def test_count_roommates_callable(self, db_session):
        assert callable(ops.count_roommates)

class TestGetActiveRentals:
    @pytest.mark.asyncio
    async def test_get_active_rentals_callable(self, db_session):
        assert callable(ops.get_active_rentals)

class TestGetByListingAndStudent:
    @pytest.mark.asyncio
    async def test_get_by_listing_and_student_callable(self, db_session):
        assert callable(ops.get_by_listing_and_student)

class TestGetByListingId:
    @pytest.mark.asyncio
    async def test_get_by_listing_id_callable(self, db_session):
        assert callable(ops.get_by_listing_id)

class TestGetByStudentId:
    @pytest.mark.asyncio
    async def test_get_by_student_id_callable(self, db_session):
        assert callable(ops.get_by_student_id)

class TestGetConversations:
    @pytest.mark.asyncio
    async def test_get_conversations_callable(self, db_session):
        assert callable(ops.get_conversations)

class TestGetMyRoomRows:
    @pytest.mark.asyncio
    async def test_get_my_room_rows_callable(self, db_session):
        assert callable(ops.get_my_room_rows)

class TestGetNeighbors:
    @pytest.mark.asyncio
    async def test_get_neighbors_callable(self, db_session):
        assert callable(ops.get_neighbors)

class TestGetOwnerRentalRows:
    @pytest.mark.asyncio
    async def test_get_owner_rental_rows_callable(self, db_session):
        assert callable(ops.get_owner_rental_rows)

class TestGetPendingByRequesterExcluding:
    @pytest.mark.asyncio
    async def test_get_pending_by_requester_excluding_callable(self, db_session):
        assert callable(ops.get_pending_by_requester_excluding)

class TestGetPendingDuplicate:
    @pytest.mark.asyncio
    async def test_get_pending_duplicate_callable(self, db_session):
        assert callable(ops.get_pending_duplicate)

class TestGetPendingForListingExcluding:
    @pytest.mark.asyncio
    async def test_get_pending_for_listing_excluding_callable(self, db_session):
        assert callable(ops.get_pending_for_listing_excluding)

class TestGetRentalById:
    @pytest.mark.asyncio
    async def test_get_rental_by_id_callable(self, db_session):
        assert callable(ops.get_rental_by_id)

class TestGetRequestById:
    @pytest.mark.asyncio
    async def test_get_request_by_id_callable(self, db_session):
        assert callable(ops.get_request_by_id)

class TestGetRequestMessages:
    @pytest.mark.asyncio
    async def test_get_request_messages_callable(self, db_session):
        assert callable(ops.get_request_messages)

class TestGetRequestsByRequester:
    @pytest.mark.asyncio
    async def test_get_requests_by_requester_callable(self, db_session):
        assert callable(ops.get_requests_by_requester)

class TestGetRequestsInbox:
    @pytest.mark.asyncio
    async def test_get_requests_inbox_callable(self, db_session):
        assert callable(ops.get_requests_inbox)

class TestGetRoomMessages:
    @pytest.mark.asyncio
    async def test_get_room_messages_callable(self, db_session):
        assert callable(ops.get_room_messages)
