from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import SessionLocal
from app.models import Users
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm


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


def authenticate_user(username: str, password: str, db):
    # Fetch user from DB
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return False  # User doesn't exist

    # Check password validity
    is_valid_password = bcrypt_context.verify(password, user.hashed_password)

    if not is_valid_password:
        return False  # Password doesn't match

    return True  # User exists and password is correct


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


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return "Failed Authentication"
    return "Successful Authentication"
