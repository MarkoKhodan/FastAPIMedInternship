import json

from quiz.models.db_models import User


def test_quiz_avarege_result(
    token, client, db_session, quiz, user, result, datetime_now
):
    response = client.get(
        "analytic/quiz_avarege_result/1", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "user_id": user.id,
            "average_result": result.average_result,
            "created_at": datetime_now,
        }
    ]


def test_employee_avarege_result(
    token, client, db_session, quiz, user, result, datetime_now
):
    response = client.get(
        "analytic/employee_avarege_result/1/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "quiz_id": quiz.id,
            "average_result": result.average_result,
            "created_at": datetime_now,
        }
    ]


def test_list_employees_last_activity(
    token, client, db_session, quiz, user, result, datetime_now, company
):
    company.employees = [user]
    db_session.commit()
    response = client.get(
        "analytic/list_employees_last_activity/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"last_activity": datetime_now, "user_id": result.user_id}
    ]


def test_user_average_result(token, client, db_session, quiz):
    data = {
        "answers": [
            {"question_id": 1, "choosed_answer_id": 1},
            {"question_id": 2, "choosed_answer_id": 4},
        ]
    }
    client.post(
        "/quiz/pass/1", json.dumps(data), headers={"Authorization": f"Bearer {token}"}
    )

    user = db_session.query(User).filter_by(id=1).first()
    response = client.get(
        "analytic/user_average_result/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "average_result": user.average_result,
        "user_id": user.id,
    }


def test_user_average_quiz_result(
    token, client, db_session, quiz, result, datetime_now
):
    data = {
        "answers": [
            {"question_id": 1, "choosed_answer_id": 1},
            {"question_id": 2, "choosed_answer_id": 3},
        ]
    }
    client.post(
        "/quiz/pass/1", json.dumps(data), headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        "analytic/user_average_quiz_result/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == [
        {"average_result": 50.0, "created_at": datetime_now},
        {"average_result": 66.66666666666666, "created_at": datetime_now},
    ]


def test_list_user_quizzes_last_activity(
    token, client, db_session, quiz, result, datetime_now
):

    response = client.get(
        "analytic/list_user_quizzes_last_activity",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == [{"last_activity": datetime_now, "quiz_id": quiz.id}]
