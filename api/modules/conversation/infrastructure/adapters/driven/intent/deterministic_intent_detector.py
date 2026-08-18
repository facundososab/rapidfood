from modules.conversation.domain.value_objects import DetectedIntent


class DeterministicIntentDetector:
    def detect(self, content: str) -> DetectedIntent:
        normalized = content.lower()
        if any(token in normalized for token in ("confirmo", "confirmar", "confirmar pedido", "dale")):
            return DetectedIntent.CONFIRM_ORDER
        if any(token in normalized for token in ("cambiar", "modificar", "agregar", "sacar", "editar")):
            return DetectedIntent.MODIFY_ORDER
        if any(token in normalized for token in ("quiero pedir", "hacer un pedido", "nuevo pedido", "pedir", "ordenar")):
            return DetectedIntent.START_ORDER
        if any(token in normalized for token in ("estado", "seguimiento", "dónde va", "donde va", "pedido")):
            return DetectedIntent.QUERY_ORDER
        if any(token in normalized for token in ("borrador", "draft")):
            return DetectedIntent.QUERY_DRAFT
        return DetectedIntent.UNKNOWN
