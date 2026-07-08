"""Integration tests for payments API endpoints."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient

from app.models.rental import Rental
from app.models.user import User
from tests.conftest import auth_headers


@pytest.fixture
async def sample_rental(db_session, student_user, active_listing):
    rental = Rental(
        listing_id=active_listing.id,
        student_id=student_user.id,
        start_date=date.today(),
        price_usd=200,
    )
    db_session.add(rental)
    await db_session.commit()
    await db_session.refresh(rental)
    return rental


@pytest.mark.asyncio
async def test_create_payment(client: AsyncClient, student_user: User, sample_rental):
    response = await client.post(
        "/api/v1/payments/",
        json={
            "rental_id": str(sample_rental.id),
            "payer_id": str(student_user.id),
            "amount": 200,
            "billing_month": str(date.today().replace(day=1)),
        },
        headers=auth_headers(student_user),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_payment_forbidden_other_user(
    client: AsyncClient,
    student_user: User,
    makler_user: User,
    sample_rental,
):
    response = await client.post(
        "/api/v1/payments/",
        json={
            "rental_id": str(sample_rental.id),
            "payer_id": str(student_user.id),
            "amount": 200,
            "billing_month": str(date.today().replace(day=1)),
        },
        headers=auth_headers(makler_user),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_payments(client: AsyncClient, student_user: User):
    response = await client.get("/api/v1/payments/", headers=auth_headers(student_user))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_payment_not_found(client: AsyncClient, student_user: User):
    response = await client.get(
        f"/api/v1/payments/{uuid.uuid4()}",
        headers=auth_headers(student_user),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_payment_status_forbidden_for_student(
    client: AsyncClient,
    student_user: User,
    sample_rental,
):
    create_resp = await client.post(
        "/api/v1/payments/",
        json={
            "rental_id": str(sample_rental.id),
            "payer_id": str(student_user.id),
            "amount": 200,
            "billing_month": str(date.today().replace(day=1)),
        },
        headers=auth_headers(student_user),
    )
    payment_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/payments/{payment_id}/status",
        json={"status": "paid"},
        headers=auth_headers(student_user),
    )
    assert response.status_code == 403
