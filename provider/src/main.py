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

# Orders database - keyed by user_id
ORDERS_DB: dict[int, list[dict]] = {}


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


class Order(BaseModel):
    """Response model for an order."""

    id: int
    user_id: int
    product: str
    quantity: int


class OrderCreate(BaseModel):
    """Request model for creating an order."""

    product: str
    quantity: int


class UserWithOrders(BaseModel):
    """Response model for a user with their orders."""

    id: int
    name: str
    email: str
    orders: list[Order]


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


@app.get("/users/{user_id}/orders", response_model=UserWithOrders)
def get_user_orders(user_id: int) -> UserWithOrders:
    """Get a user with their orders."""
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="User not found")

    user = USERS_DB[user_id]
    orders = ORDERS_DB.get(user_id, [])

    return UserWithOrders(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        orders=[Order(**order) for order in orders],
    )


@app.post("/users/{user_id}/orders", response_model=Order, status_code=201)
def create_order(user_id: int, order: OrderCreate) -> Order:
    """Create a new order for a user."""
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id not in ORDERS_DB:
        ORDERS_DB[user_id] = []

    # Generate new order ID
    all_orders = [o for orders in ORDERS_DB.values() for o in orders]
    new_id = max((o["id"] for o in all_orders), default=0) + 1

    new_order = {
        "id": new_id,
        "user_id": user_id,
        "product": order.product,
        "quantity": order.quantity,
    }
    ORDERS_DB[user_id].append(new_order)

    return Order(**new_order)
