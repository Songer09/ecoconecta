import pytest

from app.language import classify


@pytest.mark.parametrize(
    "text",
    [
        "¿Hay algún encuentro donde expliquen cómo armar una compostera?",
        "Me gustaría ir a una sesión donde aprendamos a preparar una compostera",
        "¿Hay una reunión en la que nos enseñen a preparar abono para el jardín?",
    ],
)
def test_indirect_training_requests_are_not_misclassified_as_compost_questions(text):
    result = classify(text)

    assert result.intent == "training"
    assert result.scope == "IN_SCOPE"

