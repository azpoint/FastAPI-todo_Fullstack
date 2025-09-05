from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import SessionLocal
from app.models import Users
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status


router = APIRouter()

# Bcrypt config
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# DB connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# Pydantic Validation model
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str


# Auth router endpoints
# Create User endpoint
@router.post("/auth/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    # Build the data before putting to the DB
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
    )

    db.add(create_user_model)
    db.commit()
