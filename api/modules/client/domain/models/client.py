from dataclasses import dataclass


@dataclass
class Client:
    id: str
    name: str
    last_name: str
    phone_number: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Name cannot be blank")
        if not self.last_name.strip():
            raise ValueError("Last name cannot be blank")
        if not self.phone_number.strip():
            raise ValueError("Phone number cannot be blank")

    @classmethod
    def create(
        cls,
        client_id: str,
        name: str,
        last_name: str,
        phone_number: str,
    ) -> "Client":
        return cls(
            id=client_id,
            name=name.strip(),
            last_name=last_name.strip(),
            phone_number=phone_number.strip(),
        )

    def update(self, name: str, last_name: str, phone_number: str) -> None:
        if not name.strip():
            raise ValueError("Name cannot be blank")
        if not last_name.strip():
            raise ValueError("Last name cannot be blank")
        if not phone_number.strip():
            raise ValueError("Phone number cannot be blank")

        self.name = name.strip()
        self.last_name = last_name.strip()
        self.phone_number = phone_number.strip()
