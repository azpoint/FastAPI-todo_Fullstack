from .utils import *
from app.routers.admin import get_db, get_current_user
from fastapi import status

app.dependency_overrides[get_db] = overrride_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_admin_read_all_authenticated(test_todo):
    response = client.get("/admin/todo")

    assert response.status_code == status.HTTP_200_OK
    user, todo = test_todo

    print(response.__dict__["_content"], f"User_ID!!!=>{user.id}")

    test_first_todo = response.json()[0]

    print(test_first_todo)

    assert test_first_todo["description"] == todo.description
    assert test_first_todo["complete"] == todo.complete
    assert test_first_todo["title"] == todo.title
    assert test_first_todo["priority"] == todo.priority
    assert test_first_todo["owner_id"] == todo.owner_id
