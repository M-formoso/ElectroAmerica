from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Verifica si el password plano coincide con el hash."""
    return pwd_context.verify(password_plano, password_hash)


def hashear_password(password: str) -> str:
    """Genera el hash de un password."""
    return pwd_context.hash(password)


def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT de acceso."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def crear_refresh_token(data: dict) -> str:
    """Crea un token JWT de refresco."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verificar_token(token: str) -> Optional[dict]:
    """Verifica y decodifica un token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
