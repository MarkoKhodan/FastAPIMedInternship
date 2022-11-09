import json


from quiz.models.db_models import Result


def test_quiz_create_update_delete(client, token, company):
    data = {
        "id": 0,
        "title": "string",
        "description": "string",
        "questions": [
            {
                "question_title": "string",
                "answers": [
                    {"answer_text": "string", "is_correct": False},
                    {"answer_text": "string", "is_correct": True},
                ],
            },
            {
                "question_title": "string",
                "answers": [
                    {"answer_text": "string", "is_correct": True},
                    {"answer_text": "string", "is_correct": False},
                ],
            },
        ],
    }
    response = client.post(
        "/quiz/create/1", json.dumps(data), headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "company": 1,
        "description": "string",
        "id": 1,
        "passing_frequency": None,
        "title": "string",
    }
    assert company.quizzes is not None

    response = client.post(
        "/quiz/delete/1/1", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204


def test_quiz_list_and_info(quiz, token, client):
    response = client.get("/quiz/1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "company": 1,
            "description": "test_descr",
            "id": 1,
            "passing_frequency": None,
            "title": "test",
        }
    ]

    response = client.get("/quiz/info/1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"description": "test_descr", "id": 1, "title": "test"}


def test_quiz_read_questions(quiz, token, client):
    response = client.get(
        "/quiz/read_question/1", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "questions": [
            {
                "answers": [
                    {"answer_text": "test", "id": 1},
                    {"answer_text": "test", "id": 2},
                ],
                "id": 1,
                "question_title": "test1",
            },
            {
                "answers": [
                    {"answer_text": "test", "id": 3},
                    {"answer_text": "test", "id": 4},
                ],
                "id": 2,
                "question_title": "test2",
            },
        ],
    }

    response = client.get("/quiz/info/2", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Quiz with id not found"}


def test_quiz_pass(quiz, token, client, db_session, datetime_now, user):
    data = {
        "answers": [
            {"question_id": 1, "choosed_answer_id": 1},
            {"question_id": 2, "choosed_answer_id": 3},
        ]
    }
    response = client.post(
        "/quiz/pass/1", json.dumps(data), headers={"Authorization": f"Bearer {token}"}
    )

    result = db_session.query(Result).filter_by(id=1).first()
    assert response.status_code == 200
    assert response.json() == {
        "attempts": 1,
        "average_result": 100.0,
        "company": 1,
        "created_at": datetime_now,
        "id": 1,
        "quiz_id": 1,
        "result": 100,
        "user": 1,
    }
    assert (
        result.user_id == 1
        and result.company_id == 1
        and result.quiz_id == 1
        and result.result == 100
        and result.correct_answers == 2
        and result.attempts == 1
        and result.average_result == 100
    )
    assert user.average_result == 100
