def test_deterministic_intent_detector_maps_keywords():
    from api.modules.conversation.infrastructure.adapters.driven.intent.deterministic_intent_detector import (
        DeterministicIntentDetector,
    )
    from api.modules.conversation.domain.value_objects import DetectedIntent

    detector = DeterministicIntentDetector()

    assert detector.detect("Quiero hacer un pedido") is DetectedIntent.START_ORDER
    assert detector.detect("Quiero cambiar mi pedido") is DetectedIntent.MODIFY_ORDER
    assert detector.detect("Confirmo mi pedido") is DetectedIntent.CONFIRM_ORDER


def test_deterministic_intent_detector_falls_back_to_unknown():
    from api.modules.conversation.infrastructure.adapters.driven.intent.deterministic_intent_detector import (
        DeterministicIntentDetector,
    )
    from api.modules.conversation.domain.value_objects import DetectedIntent

    detector = DeterministicIntentDetector()

    assert detector.detect("hola") is DetectedIntent.UNKNOWN
