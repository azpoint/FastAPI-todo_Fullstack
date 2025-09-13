from .utils import *
from app.routers.auth import (
    get_db,
    authenticate_user,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)
from jose import jwt
from datetime import timedelta


app.dependency_overrides[get_db] = overrride_get_db


# Test authenticate user
def test_authenticate_user(test_user):
    db = TestingSessionLocal()

    authenticated_user = authenticate_user(test_user.username, "fakepassword", db)

    assert authenticated_user is not None
    assert authenticated_user.username == test_user.username

    # Test incorrect username
    non_existing_user = authenticate_user("wrong_username", "fakepassword", db)

    assert non_existing_user is False

    # Test wrong password
    wrong_password_user = authenticate_user(test_user.username, "wrong_password", db)

    assert wrong_password_user is False


# Test create access token
def test_create_access_token():
    username = "testuser"
    user_id = 1
    role = "user"
    expires_delta = timedelta(days=1)

    token = create_access_token(username, user_id, role, expires_delta)

    decoded_token = jwt.decode(
        token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False}
    )

    assert decoded_token["sub"] == username
    assert decoded_token["id"] == user_id
    assert decoded_token["role"] == role
