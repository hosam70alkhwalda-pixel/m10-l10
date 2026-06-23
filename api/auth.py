import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Dev fixture — username: password (plain text for dev only)
USERS_DB = {
    "admin": "admin",
    "demo": "demo",
    "stretch": "stretch",
}


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    valid_key = os.getenv("API_KEY_VALID")
    if not api_key or api_key != valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


def verify_jwt(token: str = Depends(oauth2_scheme)) -> dict:
    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET not configured",
        )
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
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
    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    if token:
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT_SECRET not configured",
            )
        try:
            payload = jwt.decode(token, secret, algorithms=[algorithm])
            return {"type": "jwt", "payload": payload}
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

    valid_key = os.getenv("API_KEY_VALID")
    if api_key and api_key == valid_key:
        return {"type": "api_key", "payload": {"sub": "service"}}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
    )


def verify_jwt_only(token: str = Depends(oauth2_scheme)) -> dict:
    """JWT-only verifier — returns 403 if API key used without JWT."""
    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT required for this endpoint",
        )
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET not configured",
        )
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, secret, algorithm=algorithm)


def authenticate_user(username: str, password: str) -> bool:
    stored_password = USERS_DB.get(username)
    if not stored_password:
        return False
    return password == stored_password