"""Comprehensive unit tests for user database operations."""

import uuid

import pytest

from app.models.user import User, UserRole
from app.utils.security import hash_password
from database.operations.delete import users as delete_users
from database.operations.insert import users as insert_users
from database.operations.select import users as select_users
from database.operations.update import users as update_users


@pytest.fixture
async def sample_user(db_session):
    user = User(
        full_name="Ops Test User",
        phone="+998901111111",
        role=UserRole.student,
        hashed_password=hash_password("pass123"),
        is_verified=False,
    )
    return await insert_users.create(db_session, user)


class TestSelectUsers:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, db_session, sample_user):
        found = await select_users.get_by_id(db_session, sample_user.id)
        assert found is not None
        assert found.id == sample_user.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        assert await select_users.get_by_id(db_session, uuid.uuid4()) is None

    @pytest.mark.asyncio
    async def test_get_by_phone_found(self, db_session, sample_user):
        found = await select_users.get_by_phone(db_session, sample_user.phone)
        assert found is not None
        assert found.phone == sample_user.phone

    @pytest.mark.asyncio
    async def test_get_by_phone_not_found(self, db_session):
        assert await select_users.get_by_phone(db_session, "+000000000000") is None

    @pytest.mark.asyncio
    async def test_get_all_includes_user(self, db_session, sample_user):
        users = await select_users.get_all(db_session)
        assert any(u.id == sample_user.id for u in users)

    @pytest.mark.asyncio
    async def test_get_by_role(self, db_session, sample_user):
        students = await select_users.get_by_role(db_session, UserRole.student)
        assert any(u.id == sample_user.id for u in students)

    @pytest.mark.asyncio
    async def test_get_verified_users_excludes_unverified(self, db_session, sample_user):
        verified = await select_users.get_verified_users(db_session)
        assert all(u.is_verified for u in verified)
        assert sample_user.id not in {u.id for u in verified}

    @pytest.mark.asyncio
    async def test_count_all(self, db_session, sample_user):
        assert await select_users.count_all(db_session) >= 1

    @pytest.mark.asyncio
    async def test_count_verified(self, db_session):
        assert await select_users.count_verified(db_session) >= 0

    @pytest.mark.asyncio
    async def test_count_by_role(self, db_session, sample_user):
        rows = await select_users.count_by_role(db_session)
        assert isinstance(rows, list)


class TestInsertUsers:
    @pytest.mark.asyncio
    async def test_create_persists_user(self, db_session):
        user = User(
            full_name="New User",
            phone="+998902222222",
            role=UserRole.makler,
            hashed_password=hash_password("x"),
        )
        created = await insert_users.create(db_session, user)
        assert created.id is not None
        assert await select_users.get_by_id(db_session, created.id) is not None


class TestUpdateUsers:
    @pytest.mark.asyncio
    async def test_verify_user(self, db_session, sample_user):
        updated = await update_users.verify_user(db_session, sample_user.id)
        assert updated is not None
        assert updated.is_verified is True

    @pytest.mark.asyncio
    async def test_update_fields_not_found(self, db_session):
        result = await update_users.update_fields(db_session, uuid.uuid4(), full_name="Ghost")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_password(self, db_session, sample_user):
        new_hash = hash_password("newpass")
        updated = await update_users.update_password(db_session, sample_user.id, new_hash)
        assert updated is not None
        assert updated.hashed_password == new_hash

    @pytest.mark.asyncio
    async def test_set_verified_false(self, db_session, sample_user):
        await update_users.verify_user(db_session, sample_user.id)
        updated = await update_users.set_verified(db_session, sample_user.id, is_verified=False)
        assert updated is not None
        assert updated.is_verified is False


class TestDeleteUsers:
    @pytest.mark.asyncio
    async def test_delete_removes_user(self, db_session, sample_user):
        user_id = sample_user.id
        await delete_users.delete(db_session, sample_user)
        assert await select_users.get_by_id(db_session, user_id) is None
