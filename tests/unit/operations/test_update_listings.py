"""Unit tests for database.operations.update.listings."""

import pytest

from database.operations.update import listings as ops


class TestActivateBasic:
    @pytest.mark.asyncio
    async def test_activate_basic_callable(self, db_session):
        assert callable(ops.activate_basic)

class TestApplyFields:
    @pytest.mark.asyncio
    async def test_apply_fields_callable(self, db_session):
        assert callable(ops.apply_fields)

class TestDecrementAvailableSpaces:
    @pytest.mark.asyncio
    async def test_decrement_available_spaces_callable(self, db_session):
        assert callable(ops.decrement_available_spaces)

class TestIncrementAvailableSpaces:
    @pytest.mark.asyncio
    async def test_increment_available_spaces_callable(self, db_session):
        assert callable(ops.increment_available_spaces)

class TestIncrementViewCount:
    @pytest.mark.asyncio
    async def test_increment_view_count_callable(self, db_session):
        assert callable(ops.increment_view_count)

class TestMarkAvailable:
    @pytest.mark.asyncio
    async def test_mark_available_callable(self, db_session):
        assert callable(ops.mark_available)

class TestMarkOccupied:
    @pytest.mark.asyncio
    async def test_mark_occupied_callable(self, db_session):
        assert callable(ops.mark_occupied)

class TestSetActiveStatus:
    @pytest.mark.asyncio
    async def test_set_active_status_callable(self, db_session):
        assert callable(ops.set_active_status)

class TestUpgradeToPremium:
    @pytest.mark.asyncio
    async def test_upgrade_to_premium_callable(self, db_session):
        assert callable(ops.upgrade_to_premium)
