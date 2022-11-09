import json

from core.auth import Auth

auth_handler = Auth()


def test_user_list_and_about_user(client):
    response = client.get("/user/")

    assert response.status_code == 200
    assert response.json() == []

    data = {
        "email": "user@example.com",
        "password": "strings",
        "confirm_password": "strings",
        "username": "string",
    }
    client.post("/user/register", json.dumps(data))

    response = client.get("/user/")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "email": "user@example.com", "username": "string"},
    ]
    response = client.get("/user/about/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "user@example.com",
        "username": "string",
    }


def test_create_update_delete_user(client):
    data = {
        "email": "user@example.com",
        "password": "strings",
        "confirm_password": "strings",
        "username": "string",
    }

    response = client.post("/user/register", json.dumps(data))
    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    assert response.json()["username"] == "string"

    incorrect_email_data = {
        "email": "userexample.com",
        "password": "strings",
        "confirm_password": "strings",
        "username": "string",
    }
    response = client.post("/user/register", json.dumps(incorrect_email_data))

    assert response.status_code == 422

    incorrect_password_data = {
        "email": "user@example.com",
        "password": "strings",
        "confirm_password": "strings123",
        "username": "string",
    }
    response = client.post("/user/register", json.dumps(incorrect_password_data))

    assert response.status_code == 401

    data_to_update = {"username": "string123", "password": "strings123"}

    token = auth_handler.encode_token("user@example.com")
    response = client.put(
        "/user/update",
        json.dumps(data_to_update),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    assert response.json()["username"] == "string123"

    response = client.delete(
        "/user/delete", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204


def test_login(client):
    data = {
        "email": "user@example.com",
        "password": "strings",
        "confirm_password": "strings",
        "username": "string",
    }

    login = client.post("/user/register", json.dumps(data))

    assert login.status_code == 201
    assert login.json()["username"] == "string"
    assert login.json()["email"] == "user@example.com"


def test_about_me_with_auth0_token(client, token):
    response = client.get("/user/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert response.json()["username"] == "string"

    wrong_token_response = client.get(
        "/user/me", headers={"Authorization": f"Bearer {token}123"}
    )

    assert wrong_token_response.status_code == 401
    assert wrong_token_response.json()["detail"] == "Invalid token"
