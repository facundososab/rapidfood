import uuid


class UuidGenerator:
    def generate(self) -> str:
        return str(uuid.uuid4())