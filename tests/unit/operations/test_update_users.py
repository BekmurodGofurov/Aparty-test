"""Unit tests for database.operations.update.users."""

import pytest

from database.operations.update import users as ops


class TestSetVerified:
    @pytest.mark.asyncio
    async def test_set_verified_callable(self, db_session):
        assert callable(ops.set_verified)

class TestUpdateFields:
    @pytest.mark.asyncio
    async def test_update_fields_callable(self, db_session):
        assert callable(ops.update_fields)

class TestUpdatePassword:
    @pytest.mark.asyncio
    async def test_update_password_callable(self, db_session):
        assert callable(ops.update_password)

class TestVerifyUser:
    @pytest.mark.asyncio
    async def test_verify_user_callable(self, db_session):
        assert callable(ops.verify_user)
