"""Consumer Contract Tests for Order API using Pact v3.

This consumer demonstrates:
- Using ONE shared state with UserConsumer: "a user with ID 1 exists"
- Having TWO unique states: "user 1 has orders" and "user 1 has no orders"
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

from pact import Pact, match
from src.client import OrderApiClient

if TYPE_CHECKING:
    pass

PACTS_DIR = Path(__file__).parent.parent / "pacts"


@pytest.fixture
def pact() -> Generator[Pact, None, None]:
    """Create a Pact instance for testing."""
    pact = Pact("OrderConsumer", "UserProvider").with_specification("V4")
    yield pact
    pact.write_file(PACTS_DIR)


class TestOrderConsumerContract:
    """Contract tests for the Order Consumer."""

    def test_get_user_orders_with_orders(self, pact: Pact) -> None:
        """Test getting a user's orders when they have orders.

        Uses shared state: "a user with ID 1 exists"
        Uses unique state: "user 1 has orders"
        """
        response_body = {
            "id": match.int(1),
            "name": match.str("Alice"),
            "email": match.str("alice@example.com"),
            "orders": match.each_like(
                {
                    "id": match.int(1),
                    "user_id": match.int(1),
                    "product": match.str("Widget"),
                    "quantity": match.int(2),
                },
            ),
        }

        (
            pact
            .upon_receiving("a request for user 1 orders when user has orders")
            .given("a user with ID 1 exists")
            .given("user 1 has orders")
            .with_request("GET", "/users/1/orders")
            .will_respond_with(200)
            .with_body(response_body, content_type="application/json")
        )

        with pact.serve() as srv, OrderApiClient(str(srv.url)) as client:
            user_with_orders = client.get_user_orders(1)
            assert user_with_orders.id == 1
            assert len(user_with_orders.orders) >= 1

    def test_get_user_orders_empty(self, pact: Pact) -> None:
        """Test getting a user's orders when they have no orders.

        Uses shared state: "a user with ID 1 exists"
        Uses unique state: "user 1 has no orders"
        """
        response_body = {
            "id": match.int(1),
            "name": match.str("Alice"),
            "email": match.str("alice@example.com"),
            "orders": [],
        }

        (
            pact
            .upon_receiving("a request for user 1 orders when user has no orders")
            .given("a user with ID 1 exists")
            .given("user 1 has no orders")
            .with_request("GET", "/users/1/orders")
            .will_respond_with(200)
            .with_body(response_body, content_type="application/json")
        )

        with pact.serve() as srv, OrderApiClient(str(srv.url)) as client:
            user_with_orders = client.get_user_orders(1)
            assert user_with_orders.id == 1
            assert user_with_orders.orders == []

    def test_create_order(self, pact: Pact) -> None:
        """Test creating a new order for a user.

        Uses only shared state: "a user with ID 1 exists"
        """
        request_body = {
            "product": "Gadget",
            "quantity": 3,
        }

        response_body = {
            "id": match.int(1),
            "user_id": match.int(1),
            "product": match.str("Gadget"),
            "quantity": match.int(3),
        }

        (
            pact
            .upon_receiving("a request to create an order for user 1")
            .given("a user with ID 1 exists")
            .with_request("POST", "/users/1/orders")
            .with_body(request_body, content_type="application/json")
            .will_respond_with(201)
            .with_body(response_body, content_type="application/json")
        )

        with pact.serve() as srv, OrderApiClient(str(srv.url)) as client:
            order = client.create_order(1, "Gadget", 3)
            assert order.product == "Gadget"
            assert order.quantity == 3
