"""Unit tests for database.operations.delete.rentals."""

import pytest

from database.operations.delete import rentals as ops


class TestDeleteRental:
    @pytest.mark.asyncio
    async def test_delete_rental_callable(self, db_session):
        assert callable(ops.delete_rental)
