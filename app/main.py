from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import User

app = FastAPI(title="PayAI")


class UserCreate(BaseModel):
    name: str
    email: str


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
    db = SessionLocal()

    try:
        new_user = User(
            name=user.name,
            email=user.email
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    finally:
        db.close()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    db = SessionLocal()

    try:
        user = db.get(User, user_id)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }

    finally:
        db.close()

@app.get("/users")
def get_users():
    db = SessionLocal()

    try:
        users = db.query(User).all()

        return [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
            for user in users
        ]

    finally:
        db.close()