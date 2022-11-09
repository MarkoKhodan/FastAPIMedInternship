import json

from quiz.models.db_models import Invite, Request


def test_create_company(client, token):
    data = {"name": "string", "description": "string"}

    response = client.post(
        "/company/create",
        json.dumps(data),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "string",
        "description": "string",
        "owner": 1,
    }


def test_update_delete_company(client, token, company):

    data_to_update = {
        "name": "string123",
        "description": "string123",
        "visibility": True,
    }

    response = client.post(
        "/company/update",
        json.dumps(data_to_update),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "string123",
        "description": "string123",
        "owner": 1,
        "visibility": True,
    }


def test_delete_company(client, token, company):
    response = client.delete(
        "/company/delete", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204


def test_company_list(client, token, company):
    response = client.get("/company/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "test",
            "description": "test_descr",
            "visibility": True,
            "owner": 1,
            "employees": [],
        }
    ]


def test_create_invite(client, token, company, db_session):
    response = client.post(
        "/company/invite/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "company": 1, "user": 1}

    invite = db_session.query(Invite).filter_by(id=1).first()

    assert invite.id == 1 and invite.company == 1 and invite.user == 1

    response = client.post(
        "/company/invite/2", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "User with id doesn't exist"}


def test_remove_from_company(client, token, company, user):
    company.employees.append(user)
    response = client.post(
        "/company/delete/1", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204
    assert company.employees == []

    response = client.post(
        "/company/delete/2", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "User with id isn't in company"}


def test_add_and_remove_admins(client, token, company, user):
    company.employees.append(user)
    response = client.post(
        "/company/admins/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert company.admins == [user]
    response = client.post(
        "/company/admins/delete/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    assert company.admins == []


def test_company_requests(client, token, test_request, user, company):
    response = client.get(
        "/company/requests", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "company": 1, "user": 1}]
    response = client.post(
        "/company/request/1", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "detail": "Request from user 1 is accepted",
        "headers": None,
    }
    assert company.employees == [user]

    response = client.post(
        "/company/request/2", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Request doesn't exist"}


def test_disaprove_request(client, token, test_request, user, company, db_session):

    response = client.post(
        "/company/invites/disapprove/1", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "detail": "Request from user 1 is disapproved",
        "headers": None,
    }
    request = db_session.query(Request).filter_by(id=1).first()
    assert company.employees == []
    assert request == None
