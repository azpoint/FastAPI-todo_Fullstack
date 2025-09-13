from .utils import *
from app.routers.admin import get_db, get_current_user
from fastapi import status
from app.models import Todos

app.dependency_overrides[get_db] = overrride_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# Test todos from admin authenticated
def test_admin_read_all_authenticated(test_todo):
    response = client.get("/admin/todo")

    assert response.status_code == status.HTTP_200_OK
    user, todo = test_todo

    test_first_todo = response.json()[0]

    assert test_first_todo["description"] == todo.description
    assert test_first_todo["complete"] == todo.complete
    assert test_first_todo["title"] == todo.title
    assert test_first_todo["priority"] == todo.priority
    assert test_first_todo["owner_id"] == todo.owner_id


# Test admin delete todos
def test_admin_delete_todo(test_todo):
    user, todo = test_todo

    response = client.delete(f"/admin/todo/{todo.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()

    model = db.query(Todos).filter(Todos.id == todo.id).first()

    assert model is None


# Test
def test_admin_delete_not_found():
    response = client.delete("/admin/todo/9999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}
