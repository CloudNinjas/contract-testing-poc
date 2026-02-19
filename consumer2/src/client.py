"""Order API Client - consumes the User Provider API for order-related operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel

if TYPE_CHECKING:
    from typing import Self


class Order(BaseModel):
    """Order model."""

    id: int
    user_id: int
    product: str
    quantity: int


class UserWithOrders(BaseModel):
    """User with their orders."""

    id: int
    name: str
    email: str
    orders: list[Order]


class OrderApiClient:
    """Client for order-related API operations."""

    def __init__(self, base_url: str) -> None:
        """Initialize the client with a base URL."""
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url)

    def get_user_orders(self, user_id: int) -> UserWithOrders:
        """Get a user with their orders."""
        response = self.client.get(f"/users/{user_id}/orders")
        response.raise_for_status()
        return UserWithOrders(**response.json())

    def create_order(self, user_id: int, product: str, quantity: int) -> Order:
        """Create a new order for a user."""
        response = self.client.post(
            f"/users/{user_id}/orders",
            json={"product": product, "quantity": quantity},
        )
        response.raise_for_status()
        return Order(**response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()
