"""User Provider API - FastAPI Application."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI(
    title="User Provider API",
    description="Simple User API for Pact Contract Testing POC",
    version="0.1.0",
)

# In-memory database for demo purposes
USERS_DB: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
}


class UserCreate(BaseModel):
    """Request model for creating a user."""

    name: str
    email: EmailStr


class User(BaseModel):
    """Response model for a user."""

    id: int
    name: str
    email: str


class UserList(BaseModel):
    """Response model for list of users."""

    users: list[User]


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/users", response_model=UserList)
def list_users() -> UserList:
    """List all users."""
    users = [User(**user) for user in USERS_DB.values()]
    return UserList(users=users)


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int) -> User:
    """Get a specific user by ID."""
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**USERS_DB[user_id])


@app.post("/users", response_model=User, status_code=201)
def create_user(user: UserCreate) -> User:
    """Create a new user."""
    new_id = max(USERS_DB.keys()) + 1 if USERS_DB else 1
    new_user = {"id": new_id, "name": user.name, "email": user.email}
    USERS_DB[new_id] = new_user
    return User(**new_user)
