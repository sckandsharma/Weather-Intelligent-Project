from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

_revoked_tokens: set[str] = set()


def revoke_token(token: str) -> None:
    _revoked_tokens.add(token)


def is_token_revoked(token: str) -> bool:
    return token in _revoked_tokens