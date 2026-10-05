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
    "route": {
        "type": "choice",
        "choice": "billing",
        "probabilities": {"billing": 0.9, "technical": 0.1},
        "confidence": 0.8,
    },
    "urgency": {
        "type": "score",
        "score": 1.6,
        "legend": {"0": "Can wait", "1": "This week", "2": "Today"},
        "probabilities": {"0": 0.1, "1": 0.2, "2": 0.7},
        "confidence": 0.6,
    },
    "angry": {"type": "noul", "noul": 0.25},
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


def test_zero_shot_classification_is_registered(mappings):
    assert mappings["ZeroShotClassification"].CATEGORY == "ApiPack/Inference"


def test_zero_shot_classification_posts_state_and_questions_to_systemone(
    pack, requests_sent
):
    pack("inference").ZeroShotClassification.execute(
        "Checkout is down.", json.dumps(QUESTIONS), "http://localhost:8082/"
    )

    assert requests_sent == [
        (
            "http://localhost:8082/v1/systemone",
            {},
            {"state": "Checkout is down.", "questions": QUESTIONS},
        )
    ]


def test_zero_shot_classification_returns_answers_as_json(pack, requests_sent):
    answers, _ = pack("inference").ZeroShotClassification.execute(
        "Checkout is down.", json.dumps(QUESTIONS), "http://localhost:8082"
    )

    assert answers == json.dumps(ANSWERS, ensure_ascii=False, indent=2)


def test_zero_shot_classification_summary_has_one_line_per_question(
    pack, requests_sent
):
    _, summary = pack("inference").ZeroShotClassification.execute(
        "Checkout is down.", json.dumps(QUESTIONS), "http://localhost:8082"
    )

    assert (
        summary == "route: billing (0.90)\nurgency: Today (1.60)\nangry: false (0.25)"
    )


@pytest.mark.parametrize(
    "question_id, expected",
    [
        ("route", ("billing", 0.9, 0.8)),
        ("urgency", ("Today", 1.6, 0.6)),
        ("angry", ("false", 0.25, 0.5)),
    ],
)
def test_zero_shot_answer_picks_value_score_and_confidence(pack, question_id, expected):
    answers = json.dumps(ANSWERS)

    assert pack("inference").ZeroShotAnswer.execute(answers, question_id) == expected


def test_zero_shot_answer_unknown_question_id_raises(pack):
    with pytest.raises(KeyError):
        pack("inference").ZeroShotAnswer.execute(json.dumps(ANSWERS), "missing")


def test_zero_shot_answer_is_registered(mappings):
    assert mappings["ZeroShotAnswer"].CATEGORY == "ApiPack/Inference"


def test_zero_shot_classification_default_questions_are_valid_json(pack):
    default = pack("inference").ZeroShotClassification.INPUT_TYPES()["required"][
        "questions"
    ][1]["default"]

    assert json.loads(default)["positive"]["type"] == "noul"


def test_zero_shot_classification_sends_model_api_key_and_images(pack, requests_sent):
    pack("inference").ZeroShotClassification.execute(
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
