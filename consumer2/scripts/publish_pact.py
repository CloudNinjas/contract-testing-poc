"""Publish Pact contracts to the Pact Broker."""

import os
import sys
from pathlib import Path

import httpx

PACTS_DIR = Path(__file__).parent.parent / "pacts"
BROKER_URL = os.getenv("PACT_BROKER_BASE_URL", "http://localhost:9292")
CONSUMER_VERSION = os.getenv("CONSUMER_VERSION", "1.0.0")
BROKER_USERNAME = os.getenv("PACT_BROKER_USERNAME", "pact")
BROKER_PASSWORD = os.getenv("PACT_BROKER_PASSWORD", "pact")


def publish_pact(pact_file: Path) -> bool:
    """Publish a single pact file to the broker."""
    # Only publish OrderConsumer pacts
    if "OrderConsumer" not in pact_file.name:
        return True

    print(f"Publishing {pact_file.name}...")

    with open(pact_file, "rb") as f:
        content = f.read()

    # Extract consumer and provider from filename
    # Format: OrderConsumer-UserProvider.json
    parts = pact_file.stem.split("-")
    if len(parts) != 2:
        print(f"  Skipping {pact_file.name} - unexpected filename format")
        return True

    consumer, provider = parts

    url = f"{BROKER_URL}/pacts/provider/{provider}/consumer/{consumer}/version/{CONSUMER_VERSION}"

    try:
        response = httpx.put(
            url,
            content=content,
            headers={"Content-Type": "application/json"},
            auth=(BROKER_USERNAME, BROKER_PASSWORD),
            timeout=30,
        )
        response.raise_for_status()
        print(f"  Published successfully!")
        return True
    except httpx.HTTPStatusError as e:
        print(f"  Failed: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main() -> int:
    """Publish all OrderConsumer pact files."""
    pact_files = list(PACTS_DIR.glob("OrderConsumer-*.json"))

    if not pact_files:
        print("No OrderConsumer pact files found in", PACTS_DIR)
        return 1

    print(f"Found {len(pact_files)} pact file(s)")
    print(f"Publishing to {BROKER_URL} as version {CONSUMER_VERSION}")
    print()

    success = all(publish_pact(f) for f in pact_files)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
