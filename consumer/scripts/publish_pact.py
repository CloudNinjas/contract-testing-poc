#!/usr/bin/env python3
"""Publish Pact files to the Pact Broker."""

import os
import sys
from pathlib import Path

import httpx


def publish_pact(
    pact_dir: Path,
    broker_url: str,
    consumer_version: str,
    branch: str = "main",
    token: str | None = None,
    username: str = "pact",
    password: str = "pact",
) -> None:
    """Publish all pact files in the directory to the broker."""
    pact_files = list(pact_dir.glob("*.json"))

    if not pact_files:
        print(f"No pact files found in {pact_dir}")
        sys.exit(1)

    # Build auth headers
    headers = {"Content-Type": "application/json"}
    auth = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        auth = (username, password)

    consumers_published: set[str] = set()

    for pact_file in pact_files:
        print(f"Publishing {pact_file.name}...")

        with open(pact_file, "rb") as f:
            content = f.read()

        # Extract consumer and provider from filename
        # Format: consumername-providername.json
        name_parts = pact_file.stem.split("-")
        consumer = name_parts[0]
        provider = "-".join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]

        url = f"{broker_url}/pacts/provider/{provider}/consumer/{consumer}/version/{consumer_version}"

        response = httpx.put(
            url,
            content=content,
            headers=headers,
            auth=auth,
        )

        if response.status_code in (200, 201):
            print(f"  Published successfully: {consumer} -> {provider}")
            consumers_published.add(consumer)
        else:
            print(f"  Failed: {response.status_code} - {response.text}")
            sys.exit(1)

    # Tag each consumer version with the branch
    for consumer in consumers_published:
        tag_url = f"{broker_url}/pacticipants/{consumer}/versions/{consumer_version}/tags/{branch}"
        tag_response = httpx.put(tag_url, headers=headers, auth=auth)
        if tag_response.status_code in (200, 201):
            print(f"  Tagged {consumer} version {consumer_version} with branch '{branch}'")
        else:
            print(f"  Warning: Could not tag with branch: {tag_response.status_code}")

    print(f"\nAll pacts published! View at: {broker_url}")


if __name__ == "__main__":
    broker_url = os.getenv("PACT_BROKER_BASE_URL", "http://pact-broker:9292")
    version = os.getenv("CONSUMER_VERSION", "1.0.0")
    branch = os.getenv("GIT_BRANCH", "main")
    token = os.getenv("PACT_BROKER_TOKEN")
    username = os.getenv("PACT_BROKER_USERNAME", "pact")
    password = os.getenv("PACT_BROKER_PASSWORD", "pact")

    pacts_dir = Path(__file__).parent.parent / "pacts"

    publish_pact(pacts_dir, broker_url, version, branch, token, username, password)
