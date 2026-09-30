from dev.problem import ProblemDetails, problem_response


def test_problem_details_model():
    problem = ProblemDetails(
        type="about:blank",
        title="Invalid file",
        status=400,
        detail="The file is too large",
        instance="/validate"
    )
    assert problem.status == 400
    assert problem.title == "Invalid file"
    assert problem.type == "about:blank"
    assert problem.detail == "The file is too large"
    assert problem.instance == "/validate"

def test_problem_response():
    response = problem_response(status=400, title="Bad Request", detail="Invalid format")
    assert response.status_code == 400
    assert response.media_type == "application/problem+json"
    # Content should be a JSON encoded string
    import json
    data = json.loads(response.body)
    assert data["title"] == "Bad Request"
    assert data["status"] == 400
    assert data["detail"] == "Invalid format"
    assert data["type"] == "about:blank"
