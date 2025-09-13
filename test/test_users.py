from .utils import *
from app.routers.users import get_db, get_current_user
from fastapi import status

app.dependency_overrides[get_db] = overrride_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# Test get User
def test_return_user(test_user):
    response = client.get("/user")

    assert response.status_code == status.HTTP_200_OK

    print(response.json())
    assert response.json()["username"] == test_user.username
    assert response.json()["email"] == test_user.email
    assert response.json()["first_name"] == test_user.first_name
    assert response.json()["last_name"] == test_user.last_name
    assert response.json()["role"] == test_user.role
    assert response.json()["phone_number"] == test_user.phone_number


# Test update user password
def test_update_passwrod_succsess(test_user):
    response = client.put(
        "/user/password",
        json={"password": "fakepassword", "new_password": "newpassword"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
