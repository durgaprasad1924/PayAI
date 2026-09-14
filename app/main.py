from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="PayAI")


class UserCreate(BaseModel):
    name: str
    email: str


users = []


@app.get("/")
def root():
    return {
        "message": "Welcome to PayAI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/users")
def create_user(user: UserCreate):
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
        "email": user.email
    }

    users.append(new_user)

    return new_user