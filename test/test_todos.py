from app.routers.todos import get_db, get_current_user
from fastapi import status
from app.models import Todos
from .utils import *


app.dependency_overrides[get_db] = overrride_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# Test for all auth todo list
def test_read_all_authenticated(test_todo):
    user, todo = test_todo

    response = client.get("/todos")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Optional: check that the todo is actually returned
    assert data[0]["title"] == todo.title
    assert data[0]["description"] == todo.description
    assert data[0]["priority"] == todo.priority
    assert data[0]["complete"] == todo.complete


# Test for a single auth todo
def test_read_one_authenticated(test_todo):
    user, todo = test_todo

    response = client.get(f"/todos/todo/{todo.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["title"] == todo.title
    assert data["description"] == todo.description
    assert data["priority"] == todo.priority
    assert data["complete"] == todo.complete


# Test for a single auth todo not found
def test_read_one_authenticated_not_found():
    response = client.get("/todos/todo/999")

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

    response = client.post("/todos/todo/", json=request_data)
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

    response = client.put(f"/todos/todo/{todo.id}", json=request_data)
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

    response = client.put(f"/todos/todo/999", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


# Test for delete todo
def test_delete_todo(test_todo):
    user, todo = test_todo

    response = client.delete(f"/todos/todo/{todo.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == todo.id).first()

    assert model is None


# Test for delete todo not found
def test_delete_todo(test_todo):

    response = client.delete(f"/todos/todo/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}
