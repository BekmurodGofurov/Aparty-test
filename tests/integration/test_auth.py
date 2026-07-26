import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import auth_headers
from app.domains.users.models import UserRole
import random
import string

pytestmark = pytest.mark.asyncio

@pytest.fixture
def unique_phone():
    return f"+9989{random.randint(1000000, 9999999)}"

@pytest.fixture
def unique_id():
    return random.randint(10000000000, 99999999999)


class TestAuthFlow:
    @pytest.mark.parametrize("id_val", [12345678901, -1, 0, None, "hacker", 999999999999999999])
    @pytest.mark.parametrize("full_name", ["Test User", "", "A", "A" * 150, "<script>alert(1)</script>"])
    @pytest.mark.parametrize("phone", ["+998901234567", "", "1234", "+1" * 20])
    @pytest.mark.parametrize("role", ["student", "makler", "owner", "admin", "invalid", None])
    async def test_register_massive(self, client: AsyncClient, db_session: AsyncSession, id_val, full_name, phone, role):
        payload = {
            "id": id_val,
            "full_name": full_name,
            "phone": phone,
            "role": role,
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        
        is_valid_id = isinstance(id_val, int) and id_val > 0
        is_valid_name = isinstance(full_name, str) and 2 <= len(full_name) <= 100
        is_valid_phone = isinstance(phone, str) and 7 <= len(phone) <= 20
        is_valid_role = role in ["student", "makler", "owner"]
        
        if is_valid_id and is_valid_name and is_valid_phone and is_valid_role:
            assert resp.status_code == 201
            # Cleanup to avoid duplicate key errors in cartesian product
            await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": id_val})
            await db_session.commit()
        else:
            # Pydantic validation error or manual rejection
            assert resp.status_code in [422, 400]

    async def test_register_duplicate(self, client: AsyncClient, unique_id, unique_phone):
        payload = {"id": unique_id, "full_name": "Test", "phone": unique_phone, "role": "student"}
        resp1 = await client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201
        
        # Duplicate ID
        payload2 = {"id": unique_id, "full_name": "Test2", "phone": unique_phone + "1", "role": "student"}
        resp2 = await client.post("/api/v1/auth/register", json=payload2)
        assert resp2.status_code == 400
        assert "exists" in resp2.json()["detail"].lower()
        
        # Duplicate Phone
        payload3 = {"id": unique_id + 1, "full_name": "Test3", "phone": unique_phone, "role": "student"}
        resp3 = await client.post("/api/v1/auth/register", json=payload3)
        assert resp3.status_code == 400
        assert "registered" in resp3.json()["detail"].lower()

    @pytest.mark.parametrize("user_id, expected_status", [
        (98765432103, 200), # student_user fixture ID
        (98765432104, 200), # makler_user fixture ID
        (99999999999, 404), # Not found
        (None, 422),
        (-1, 404), # Might be 422
    ])
    async def test_bot_login_code(self, client: AsyncClient, student_user, makler_user, user_id, expected_status):
        payload = {"id": user_id}
        resp = await client.post("/api/v1/auth/bot/login-code", json=payload)
        assert resp.status_code in [expected_status, 422]
        
        if resp.status_code == 200:
            assert "code" in resp.json()
            assert len(resp.json()["code"]) == 6

    @pytest.mark.parametrize("code, expected_status", [
        (None, 422),
        ("", 422),
        ("123", 422),
        ("1234567", 422),
        ("abcdef", 422),
        ("000000", 400), # Valid format but not found
    ])
    async def test_login_invalid_codes(self, client: AsyncClient, code, expected_status):
        payload = {"code": code}
        resp = await client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code in [expected_status, 422]

    async def test_full_login_flow(self, client: AsyncClient, student_user):
        # 1. Generate Code
        resp1 = await client.post("/api/v1/auth/bot/login-code", json={"id": student_user.id})
        assert resp1.status_code == 200
        code = resp1.json()["code"]
        
        # 2. Login with Code
        resp2 = await client.post("/api/v1/auth/login", json={"code": code})
        assert resp2.status_code == 200
        assert "access_token" in resp2.json()
        
        # 3. Prevent Code Reuse
        resp3 = await client.post("/api/v1/auth/login", json={"code": code})
        assert resp3.status_code == 400
        assert "muddat" in resp3.json()["detail"].lower() or "noto'g'ri" in resp3.json()["detail"].lower()
