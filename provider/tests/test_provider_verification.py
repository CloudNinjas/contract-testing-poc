"""Provider Verification Tests using Pact v3.

These tests verify that the Provider API fulfills the contracts
defined by its Consumers. The Pact verifier replays the consumer
interactions against the running provider and checks the responses.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, Literal

import pytest
import uvicorn

from pact import Verifier
from src.main import ORDERS_DB, USERS_DB, app

if TYPE_CHECKING:
    from typing import TypeAlias

    ACTION_TYPE: TypeAlias = Literal["setup", "teardown"]

logger = logging.getLogger(__name__)

PACTS_DIR = Path(__file__).parent.parent / "pacts"


@pytest.fixture(scope="session")
def provider_url() -> str:
    """Start the FastAPI provider in a background thread."""
    host = "localhost"
    port = 8080

    thread = Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": host, "port": port, "log_level": "warning"},
        daemon=True,
    )
    thread.start()

    # Give the server a moment to start
    import time
    time.sleep(1)

    return f"http://{host}:{port}"


def test_provider_against_pact(provider_url: str) -> None:
    """Verify the provider fulfills all consumer contracts."""
    broker_url = os.getenv("PACT_BROKER_BASE_URL")

    verifier = Verifier("UserProvider").add_transport(url=provider_url)

    if broker_url:
        # Verify against Pact Broker
        broker_token = os.getenv("PACT_BROKER_TOKEN")
        if broker_token:
            verifier = verifier.broker_source(
                broker_url,
                token=broker_token,
            )
        else:
            verifier = verifier.broker_source(
                broker_url,
                username=os.getenv("PACT_BROKER_USERNAME", "pact"),
                password=os.getenv("PACT_BROKER_PASSWORD", "pact"),
            )
        # Publish verification results back to broker
        provider_version = os.getenv("PROVIDER_VERSION", "0.1.0")
        verifier = verifier.set_publish_options(
            version=provider_version,
            url=broker_url,
        )
    else:
        # Verify against local pact files
        verifier = verifier.add_source(PACTS_DIR)

    verifier = verifier.state_handler(
        {
            # Shared states (used by UserConsumer and OrderConsumer)
            "a user with ID 1 exists": state_user_exists,
            # UserConsumer only
            "no user with ID 999 exists": state_user_not_exists,
            "users exist in the system": state_users_exist,
            "the system is ready to create users": state_ready_to_create,
            # OrderConsumer only
            "user 1 has orders": state_user_has_orders,
            "user 1 has no orders": state_user_has_no_orders,
        },
        teardown=True,
    )

    verifier.verify()


# ---------------------------------------------------------------------------
# Provider State Handlers
# ---------------------------------------------------------------------------

def state_user_exists(
    action: Literal["setup", "teardown"],
    parameters: dict[str, Any],
) -> None:
    """Ensure a user with ID 1 exists in the database."""
    if action == "setup":
        USERS_DB[1] = {"id": 1, "name": "Alice", "email": "alice@example.com"}
    elif action == "teardown":
        with contextlib.suppress(KeyError):
            del USERS_DB[1]


def state_user_not_exists(
    action: Literal["setup", "teardown"],
    parameters: dict[str, Any],
) -> None:
    """Ensure user 999 does NOT exist in the database."""
    if action == "setup":
        USERS_DB.pop(999, None)


def state_users_exist(
    action: Literal["setup", "teardown"],
    parameters: dict[str, Any],
) -> None:
    """Ensure at least one user exists in the database."""
    if action == "setup":
        if not USERS_DB:
            USERS_DB[1] = {"id": 1, "name": "Alice", "email": "alice@example.com"}


def state_ready_to_create(
    action: Literal["setup", "teardown"],
    parameters: dict[str, Any],
) -> None:
    """No special setup needed - system is ready for user creation."""


def state_user_has_orders(
    action: Literal["setup", "teardown"],
    parameters: dict[str, Any],
) -> None:
    """Ensure user 1 has orders in the database."""
    if action == "setup":
        ORDERS_DB[1] = [
            {"id": 1, "user_id": 1, "product": "Widget", "quantity": 2},
            {"id": 2, "user_id": 1, "product": "Gadget", "quantity": 1},
        ]
    elif action == "teardown":
        ORDERS_DB.pop(1, None)


def state_user_has_no_orders(
    action: Literal["setup", "teardown"],
    parameters: dict[str, Any],
) -> None:
    """Ensure user 1 has NO orders in the database."""
    if action == "setup":
        ORDERS_DB.pop(1, None)
