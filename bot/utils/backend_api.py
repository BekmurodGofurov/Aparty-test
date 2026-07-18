"""Backend API client for interacting with the FastAPI backend.

The Bot is a pure client — identical in role to the React frontend.
It sends HTTP requests to the backend; the backend never contacts Telegram.
"""
import httpx
from typing import Optional, Dict, Any
from config.settings import settings


class BackendAPIClient:
    """Client for communicating with the backend API."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.BACKEND_URL

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the backend."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return {"success": True, "data": response.json()}
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                detail = error_data.get("detail", str(e))

                # Extract message from Pydantic validation errors (422)
                if isinstance(detail, list) and len(detail) > 0:
                    error_obj = detail[0]
                    error_msg = error_obj.get("msg", str(error_obj)) if isinstance(error_obj, dict) else str(error_obj)
                else:
                    error_msg = str(detail) if detail else f"HTTP {e.response.status_code}"

                return {"success": False, "error": error_msg}
            except Exception:
                return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Ulanish xatosi: {str(e)}"}

    # ── Registration ─────────────────────────────────────────────────────────

    async def check_user_by_telegram_id(self, telegram_id: int) -> Dict[str, Any]:
        """Check if a user with this Telegram ID is registered in the backend.

        The backend looks up users.id == telegram_id (BigInteger PK).
        """
        return await self._make_request("GET", f"/api/v1/auth/bot/check/{telegram_id}")

    async def register_user(
        self,
        telegram_id: int,
        full_name: str,
        phone: str,
        role: str,
    ) -> Dict[str, Any]:
        """Register a new user.

        Sends the Telegram ID as `id` — the backend stores it as the primary key.
        No password is sent; authentication uses the login-code flow.
        """
        payload = {
            "id": telegram_id,
            "full_name": full_name,
            "phone": phone,
            "role": role,
        }
        return await self._make_request("POST", "/api/v1/auth/register", json=payload)

    # ── Login Code ───────────────────────────────────────────────────────────

    async def request_login_code(self, telegram_id: int) -> Dict[str, Any]:
        """Ask the backend to generate a 6-digit login code for this user.

        The backend stores the code in memory (2-min TTL, single-use) and
        returns it in the response.  The bot then displays it to the user.
        The backend never sends it — the bot is the display layer.
        """
        return await self._make_request(
            "POST",
            "/api/v1/auth/bot/login-code",
            json={"id": telegram_id},
        )


# Global client instance
backend_client = BackendAPIClient()
