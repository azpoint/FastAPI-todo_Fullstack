from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from fastapi.testclient import TestClient
import pytest
from app.models import Todos, Users
from app.routers.auth import bcrypt_context

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:todoApp@localhost:5432/test_db"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def overrride_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {"username": "sweet", "id": 1, "user_role": "admin"}


client = TestClient(app)


@pytest.fixture
def test_todo():
    db = TestingSessionLocal()

    user = Users(
        id=1,
        email="test@mail.com",
        username="sweet",
        first_name="Sweet",
        last_name="Doe",
        hashed_password="fakepassword",
        is_active=True,
        role="admin",
        phone_number="555-55-55",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    todo = Todos(
        title="Learn to code!",
        description="Need to learn everyday!",
        priority=5,
        complete=False,
        owner_id=user.id,
    )

    db.add(todo)
    db.commit()
    db.refresh(todo)

    yield user, todo

    db.query(Todos).delete()
    db.query(Users).delete()
    db.commit()
    db.close()


@pytest.fixture
def test_user():
    user = Users(
        id=1,
        email="test@mail.com",
        username="sweet",
        first_name="Sweet",
        last_name="Doe",
        hashed_password=bcrypt_context.hash("fakepassword"),
        is_active=True,
        role="admin",
        phone_number="555-55-55",
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()

    yield user

    db.query(Users).delete()
    db.commit()
    db.close()
