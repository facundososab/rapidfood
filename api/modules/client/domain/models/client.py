from dataclasses import dataclass


@dataclass
class Client:
    id: str
    name: str
    lastName: str
    phoneNumber: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Name cannot be blank")
        if not self.lastName.strip():
            raise ValueError("Last name cannot be blank")
        if not self.phoneNumber.strip():
            raise ValueError("Phone number cannot be blank")

    @property
    def last_name(self) -> str:
        return self.lastName

    @last_name.setter
    def last_name(self, value: str) -> None:
        self.lastName = value

    @property
    def phone_number(self) -> str:
        return self.phoneNumber

    @phone_number.setter
    def phone_number(self, value: str) -> None:
        self.phoneNumber = value

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
            lastName=last_name.strip(),
            phoneNumber=phone_number.strip(),
        )

    def update(self, name: str, last_name: str, phone_number: str) -> None:
        if not name.strip():
            raise ValueError("Name cannot be blank")
        if not last_name.strip():
            raise ValueError("Last name cannot be blank")
        if not phone_number.strip():
            raise ValueError("Phone number cannot be blank")

        self.name = name.strip()
        self.lastName = last_name.strip()
        self.phoneNumber = phone_number.strip()
