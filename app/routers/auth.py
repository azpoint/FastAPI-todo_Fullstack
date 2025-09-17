from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.database import SessionLocal
from app.models import Users
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix="/auth", tags=["auth"])

#### Logic #####


# Pydantic Validation model
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    token_type: str


# JWT config
SECRET_KEY = "577cbac60a39b328ec731b5d31475a27e40d5e3cad0600acc8584098bc9165bf"
ALGORITHM = "HS256"

# Bcrypt config
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


# DB connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

templates = Jinja2Templates(directory="templates")


# Pages
@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# Endpoints
def authenticate_user(username: str, password: str, db):
    # Fetch user from DB
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return False  # User doesn't exist

    # Check password validity
    valid_password = bcrypt_context.verify(password, user.hashed_password)

    if not valid_password:
        return False  # Password doesn't match

    return user  # User exists and password is correct


# JWT create/encode token
def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):

    encode = {"sub": username, "id": user_id, "role": role}

    expires = datetime.now(timezone.utc) + expires_delta

    encode.update({"exp": expires})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# JWT decode token.
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )

        return {"username": username, "id": user_id, "user_role": user_role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
        )


#### Auth Endpoints #####
# Create User endpoint
@router.post("/", status_code=status.HTTP_201_CREATED)
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
        phone_number=create_user_request.phone_number,
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
        )

    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=20)
    )

    return {"access_token": token, "token_type": "bearer"}
