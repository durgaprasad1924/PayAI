import secrets


def generate_registration_token() -> str:
    """
    Generate a cryptographically secure registration token.
    """

    return secrets.token_urlsafe(32)