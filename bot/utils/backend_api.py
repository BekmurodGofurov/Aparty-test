"""Backend API client for interacting with the main server"""
import httpx
from typing import Optional, Dict, Any
from config.settings import settings


class BackendAPIClient:
    """Client for communicating with the backend API"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.BACKEND_URL

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to backend"""
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
                
                # Extract error message from Pydantic validation errors (422)
                if isinstance(detail, list) and len(detail) > 0:
                    error_obj = detail[0]
                    if isinstance(error_obj, dict):
                        error_msg = error_obj.get("msg", str(detail))
                    else:
                        error_msg = str(error_obj)
                else:
                    error_msg = str(detail) if detail else f"HTTP {e.response.status_code}"
                
                return {"success": False, "error": error_msg}
            except Exception:
                return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Ulanish xatosi: {str(e)}"}

    async def check_user_by_telegram_id(self, telegram_id: int) -> Dict[str, Any]:
        """Check if user with given Telegram ID exists in backend"""
        return await self._make_request("GET", f"/api/v1/auth/bot/check/{telegram_id}")

    async def register_user(
        self,
        full_name: str,
        phone: str,
        role: str,
        password: str,
        user_id: int,
        university: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register new user with backend"""
        # Map bot roles to backend role IDs
        # student: 1, owner: 2, makler: 3, admin: 4
        role_mapping = {
            "tenant": 1,
            "student": 1,
            "owner": 2,
            "apartment_owner": 2,
            "realtor": 3,
            "makler": 3,
            "admin": 4
        }

        role_id = role_mapping.get(role, 1)

        payload = {
            "user_id": user_id,
            "full_name": full_name,
            "phone": phone,
            "role_id": role_id,
            "password": password,
        }

        if university:
            payload["university"] = university

        return await self._make_request("POST", "/api/v1/auth/register", json=payload)


# Global client instance
backend_client = BackendAPIClient()
