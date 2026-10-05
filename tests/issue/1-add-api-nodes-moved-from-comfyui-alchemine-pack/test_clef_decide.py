import json
import types

import pytest
import torch

QUESTIONS = {
    "urgency": {
        "type": "score",
        "instructions": "How urgent is it?",
        "criteria": ["Can wait", "This week", "Today"],
    }
}
ANSWERS = {
    "urgency": {"score": 2.4, "confidence": 0.8, "probabilities": [0.1, 0.4, 0.5]}
}


@pytest.fixture
def requests_sent(pack, monkeypatch):
    sent = []

    def post(url, headers, json, timeout):
        sent.append((url, headers, json))
        return types.SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"model": "clef-flash", "answers": ANSWERS, "usage": {}},
        )

    monkeypatch.setattr(pack("inference")._session, "post", post)
    return sent


def test_clef_decide_is_registered(mappings):
    assert mappings["ClefDecide"].CATEGORY == "ApiPack/Inference"


def test_clef_decide_posts_state_and_questions_to_systemone(pack, requests_sent):
    pack("inference").ClefDecide.execute(
        "Checkout is down.", json.dumps(QUESTIONS), "http://localhost:8082/"
    )

    assert requests_sent == [
        (
            "http://localhost:8082/v1/systemone",
            {},
            {"state": "Checkout is down.", "questions": QUESTIONS},
        )
    ]


def test_clef_decide_returns_answers_as_json(pack, requests_sent):
    (answers,) = pack("inference").ClefDecide.execute(
        "Checkout is down.", json.dumps(QUESTIONS), "http://localhost:8082"
    )

    assert json.loads(answers) == ANSWERS


def test_clef_decide_default_questions_are_valid_json(pack):
    default = pack("inference").ClefDecide.INPUT_TYPES()["required"]["questions"][1][
        "default"
    ]

    assert json.loads(default)["positive"]["type"] == "noul"


def test_clef_decide_sends_model_api_key_and_images(pack, requests_sent):
    pack("inference").ClefDecide.execute(
        "A picture.",
        json.dumps(QUESTIONS),
        "http://localhost:8082",
        api_key="secret",
        model="clef-flash",
        image=torch.zeros(2, 8, 8, 3),
    )

    ((_, headers, payload),) = requests_sent
    assert headers == {"Authorization": "Bearer secret"}
    assert payload["model"] == "clef-flash"
    assert len(payload["images"]) == 2
    assert all(i.startswith("data:image/png;base64,") for i in payload["images"])
