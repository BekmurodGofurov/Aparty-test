"""Unit tests for database.operations.select.reviews."""

import pytest

from database.operations.select import reviews as ops


class TestCountByListing:
    @pytest.mark.asyncio
    async def test_count_by_listing_callable(self, db_session):
        assert callable(ops.count_by_listing)

class TestGetAverageRating:
    @pytest.mark.asyncio
    async def test_get_average_rating_callable(self, db_session):
        assert callable(ops.get_average_rating)

class TestGetByAuthorId:
    @pytest.mark.asyncio
    async def test_get_by_author_id_callable(self, db_session):
        assert callable(ops.get_by_author_id)

class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_callable(self, db_session):
        assert callable(ops.get_by_id)

class TestGetByListingAndAuthor:
    @pytest.mark.asyncio
    async def test_get_by_listing_and_author_callable(self, db_session):
        assert callable(ops.get_by_listing_and_author)

class TestGetByListingId:
    @pytest.mark.asyncio
    async def test_get_by_listing_id_callable(self, db_session):
        assert callable(ops.get_by_listing_id)

class TestGetByListingWithAuthor:
    @pytest.mark.asyncio
    async def test_get_by_listing_with_author_callable(self, db_session):
        assert callable(ops.get_by_listing_with_author)

class TestGetListingReviewsWithAuthors:
    @pytest.mark.asyncio
    async def test_get_listing_reviews_with_authors_callable(self, db_session):
        assert callable(ops.get_listing_reviews_with_authors)

class TestGetWithAuthor:
    @pytest.mark.asyncio
    async def test_get_with_author_callable(self, db_session):
        assert callable(ops.get_with_author)
