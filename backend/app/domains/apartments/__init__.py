"""Apartments domain package."""

def register_event_handlers() -> None:
    from app.core.events import subscribe
    from app.domains.apartments.services import handle_order_placed
    subscribe("order.placed", handle_order_placed)
