"""Small, platform independent validation functions."""


def validate_workers(value: object, maximum: int = 16) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("workers must be an integer")
    if not 1 <= value <= maximum:
        raise ValueError(f"workers must be between 1 and {maximum}")
    return value


def validate_name(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("service.name must be a non-empty string")
    return value.strip()

