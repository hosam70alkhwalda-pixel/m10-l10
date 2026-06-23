import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

USERS_DB = {
    "admin": "admin",
    "demo": "demo",
    "stretch": "stretch",
}

_DEFAULT_SECRET = "super-secret-key-change-in-production-2024"
_DEFAULT_API_KEY = "ci-test-api-key"


def _get_secret() -> str:
    return os.getenv("JWT_SECRET") or _DEFAULT_SECRET

def _get_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")

def _get_api_key() -> str:
    return os.getenv("API_KEY_VALID") or _DEFAULT_API_KEY


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    valid_key = _get_api_key()
    if not api_key or api_key != valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


def verify_jwt(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[_get_algorithm()])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def verify_api_key_or_jwt(
    api_key: str = Security(api_key_header),
    token: str = Depends(oauth2_scheme),
) -> dict:
    if token:
        try:
            payload = jwt.decode(token, _get_secret(), algorithms=[_get_algorithm()])
            return {"type": "jwt", "payload": payload}
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

    if api_key and api_key == _get_api_key():
        return {"type": "api_key", "payload": {"sub": "service"}}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
    )


def verify_jwt_only(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT required for this endpoint",
        )
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[_get_algorithm()])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, _get_secret(), algorithm=_get_algorithm())


def authenticate_user(username: str, password: str) -> bool:
    stored_password = USERS_DB.get(username)
    if not stored_password:
        return False
    return password == stored_password