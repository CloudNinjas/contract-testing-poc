"""Consumer Contract Tests using Pact v3.

These tests define what the Consumer expects from the Provider API.
Running these tests generates a Pact file (contract) that can be
verified against the actual Provider.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

from pact import Pact, match
from src.client import UserApiClient

if TYPE_CHECKING:
    from collections.abc import Generator

PACTS_DIR = Path(__file__).parent.parent / "pacts"


@pytest.fixture
def pact() -> Generator[Pact, None, None]:
    """Set up a Pact mock provider for consumer tests."""
    pact = Pact("UserConsumer", "UserProvider").with_specification("V4")
    yield pact
    pact.write_file(PACTS_DIR)


class TestGetUser:
    """Contract tests for GET /users/{id}."""

    def test_get_existing_user(self, pact: Pact) -> None:
        """Test fetching an existing user returns expected fields."""
        response_body = {
            "id": match.int(1),
            "name": match.str("Alice"),
            "email": match.str("alice@example.com"),
        }

        (
            pact
            .upon_receiving("a request for user 1")
            .given("a user with ID 1 exists", id=1, name="Alice")
            .with_request("GET", "/users/1")
            .will_respond_with(200)
            .with_body(response_body, content_type="application/json")
        )

        with pact.serve() as srv, UserApiClient(str(srv.url)) as client:
            user = client.get_user(1)
            assert user.id == 1
            assert user.name == "Alice"
            assert user.email == "alice@example.com"

    def test_get_nonexistent_user(self, pact: Pact) -> None:
        """Test fetching a user that doesn't exist returns 404."""
        (
            pact
            .upon_receiving("a request for a non-existent user")
            .given("no user with ID 999 exists")
            .with_request("GET", "/users/999")
            .will_respond_with(404)
            .with_body(
                {"detail": "User not found"},
                content_type="application/json",
            )
        )

        with (
            pact.serve() as srv,
            UserApiClient(str(srv.url)) as client,
            pytest.raises(httpx.HTTPStatusError),
        ):
            client.get_user(999)


class TestListUsers:
    """Contract tests for GET /users."""

    def test_list_users(self, pact: Pact) -> None:
        """Test listing all users returns a list."""
        response_body = {
            "users": match.each_like(
                {
                    "id": match.int(1),
                    "name": match.str("Alice"),
                    "email": match.str("alice@example.com"),
                },
            ),
        }

        (
            pact
            .upon_receiving("a request to list all users")
            .given("users exist in the system")
            .with_request("GET", "/users")
            .will_respond_with(200)
            .with_body(response_body, content_type="application/json")
        )

        with pact.serve() as srv, UserApiClient(str(srv.url)) as client:
            users = client.list_users()
            assert len(users) >= 1
            assert users[0].id is not None
            assert users[0].name is not None


class TestCreateUser:
    """Contract tests for POST /users."""

    def test_create_user(self, pact: Pact) -> None:
        """Test creating a new user."""
        request_body = {
            "name": "Charlie",
            "email": "charlie@example.com",
        }

        response_body = {
            "id": match.int(3),
            "name": "Charlie",
            "email": "charlie@example.com",
        }

        (
            pact
            .upon_receiving("a request to create a new user")
            .given("the system is ready to create users")
            .with_request("POST", "/users")
            .with_body(request_body, content_type="application/json")
            .will_respond_with(201)
            .with_body(response_body, content_type="application/json")
        )

        with pact.serve() as srv, UserApiClient(str(srv.url)) as client:
            from src.client import UserCreate

            new_user = UserCreate(name="Charlie", email="charlie@example.com")
            created = client.create_user(new_user)
            assert created.name == "Charlie"
            assert created.email == "charlie@example.com"
