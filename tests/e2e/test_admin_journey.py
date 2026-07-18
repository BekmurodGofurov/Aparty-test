"""E2E Scenario 3: Admin logs in -> moderates listing -> bans user."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_headers


from app.utils.login_code_store import generate_login_code


@pytest.mark.asyncio
async def test_admin_journey_moderate_and_ban(
    client: AsyncClient,
    admin_user: User,
    active_listing,
    student_user: User,
):
    admin_headers = auth_headers(admin_user)

    code = generate_login_code(str(admin_user.id))
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"code": code},
    )
    assert login_response.status_code == 200

    dashboard = await client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["listings"] >= 1

    deactivate = await client.patch(
        f"/api/v1/admin/listings/{active_listing.id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["listing"]["is_active"] is False

    ban_user = await client.patch(
        f"/api/v1/admin/users/{student_user.id}/status",
        json={"is_verified": False},
        headers=admin_headers,
    )
    assert ban_user.status_code == 200
    assert ban_user.json()["user"]["is_verified"] is False

    detail = await client.get(
        f"/api/v1/admin/users/{student_user.id}/detail",
        headers=admin_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["user"]["id"] == student_user.id
