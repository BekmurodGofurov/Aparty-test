"""Read-only Pydantic DTOs representing user identity for cross-domain use.

These are the ONLY user-related types that the ``apartments`` and ``orders``
domains are allowed to import. They carry no SQLAlchemy dependency.
"""

from __future__ import annotations

from pydantic import BaseModel


class UserIdentityDTO(BaseModel):
    """Minimal user identity data needed by other domains."""

    id: int
    full_name: str
    phone: str
    is_verified: bool
    role: str
