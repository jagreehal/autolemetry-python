"""FastAPI example with autolemetry."""

from typing import Any

from fastapi import FastAPI

from autolemetry.integrations.fastapi import AutolemetryMiddleware

app = FastAPI()

# Add autolemetry middleware
app.add_middleware(AutolemetryMiddleware, service="fastapi-example")


@app.get("/")
def read_root() -> None:
    """Root endpoint."""
    return {"message": "Hello World"}


@app.get("/users/{user_id}")
def get_user(user_id: int) -> None:
    """Get user by ID."""
    return {"user_id": user_id, "name": "John Doe"}


@app.post("/users")
def create_user(user_data: dict[str, Any]) -> None:
    """Create a new user."""
    return {"id": 123, **user_data}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
