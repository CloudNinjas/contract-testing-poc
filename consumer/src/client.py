"""User API Client - Consumer implementation."""

import httpx
from pydantic import BaseModel


class User(BaseModel):
    """User model."""

    id: int
    name: str
    email: str


class UserCreate(BaseModel):
    """Model for creating a user."""

    name: str
    email: str


class UserApiClient:
    """Client for the User Provider API."""

    def __init__(self, base_url: str) -> None:
        """Initialize the client with a base URL."""
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url)

    def get_user(self, user_id: int) -> User:
        """Fetch a user by ID."""
        response = self.client.get(f"/users/{user_id}")
        response.raise_for_status()
        return User(**response.json())

    def list_users(self) -> list[User]:
        """Fetch all users."""
        response = self.client.get("/users")
        response.raise_for_status()
        data = response.json()
        return [User(**user) for user in data["users"]]

    def create_user(self, user: UserCreate) -> User:
        """Create a new user."""
        response = self.client.post("/users", json=user.model_dump())
        response.raise_for_status()
        return User(**response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "UserApiClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()
