from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.routers.todos import get_db, get_current_user
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from app.models import Todos, Users


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


app.dependency_overrides[get_db] = overrride_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

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


# Test for all auth todo list
def test_read_all_authenticated(test_todo):
    user, todo = test_todo

    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Optional: check that the todo is actually returned
    assert len(data) == 1
    assert data[0]["title"] == todo.title
    assert data[0]["description"] == todo.description
    assert data[0]["priority"] == todo.priority
    assert data[0]["complete"] == todo.complete


# Test for a single auth todo
def test_read_one_authenticated(test_todo):
    user, todo = test_todo

    response = client.get(f"/todo/{todo.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["title"] == todo.title
    assert data["description"] == todo.description
    assert data["priority"] == todo.priority
    assert data["complete"] == todo.complete


# Test for a single auth todo not found
def test_read_one_authenticated_not_found():
    response = client.get("/todo/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


# Test create todo
def test_create_todo(test_todo):
    user, todo = test_todo

    request_data = {
        "title": "New Todo!",
        "description": "New description",
        "priority": 5,
        "complete": False,
        "owner_id": user.id,
    }

    response = client.post("/todo/", json=request_data)
    assert response.status_code == 201

    created_todo = response.json()

    db = TestingSessionLocal()

    model = db.query(Todos).filter(Todos.id == created_todo["id"]).first()

    assert model.title == request_data.get("title")
    assert model.description == request_data.get("description")
    assert model.priority == request_data.get("priority")
    assert model.complete == request_data.get("complete")


# Test for update todo
def test_update_todo(test_todo):
    user, todo = test_todo

    request_data = {
        "title": "Update todo!",
        "description": "Update description",
        "priority": 3,
        "complete": False,
    }

    response = client.put(f"/todo/{todo.id}", json=request_data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()

    model = db.query(Todos).filter(Todos.id == todo.id).first()

    assert model.title == request_data["title"]
    assert model.description == request_data["description"]
    assert model.priority == request_data["priority"]
    assert model.complete == request_data["complete"]


# Test for update todo not found
def test_update_todo_not_found(test_todo):

    request_data = {
        "title": "Update todo!",
        "description": "Update description",
        "priority": 3,
        "complete": False,
    }

    response = client.put(f"/todo/999", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


# Test for delete todo
def test_delete_todo(test_todo):
    user, todo = test_todo

    response = client.delete(f"/todo/{todo.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == todo.id).first()

    assert model is None


# Test for delete todo not found
def test_delete_todo(test_todo):

    response = client.delete(f"/todo/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}
