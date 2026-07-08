"""Unit tests for database.operations.select.users."""

import pytest

from database.operations.select import users as ops


class TestCountAll:
    @pytest.mark.asyncio
    async def test_count_all_callable(self, db_session):
        assert callable(ops.count_all)

class TestCountByRole:
    @pytest.mark.asyncio
    async def test_count_by_role_callable(self, db_session):
        assert callable(ops.count_by_role)

class TestCountVerified:
    @pytest.mark.asyncio
    async def test_count_verified_callable(self, db_session):
        assert callable(ops.count_verified)

class TestGetAll:
    @pytest.mark.asyncio
    async def test_get_all_callable(self, db_session):
        assert callable(ops.get_all)

class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_callable(self, db_session):
        assert callable(ops.get_by_id)

class TestGetByPhone:
    @pytest.mark.asyncio
    async def test_get_by_phone_callable(self, db_session):
        assert callable(ops.get_by_phone)

class TestGetByRole:
    @pytest.mark.asyncio
    async def test_get_by_role_callable(self, db_session):
        assert callable(ops.get_by_role)

class TestGetVerifiedUsers:
    @pytest.mark.asyncio
    async def test_get_verified_users_callable(self, db_session):
        assert callable(ops.get_verified_users)
