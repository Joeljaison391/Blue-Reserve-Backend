# jwt_handler.py
from jose import jwt, JWTError
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("jwt_handler")

SECRET_KEY = "your_secret_key"  # Replace with a strong secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Generated JWT Token: {encoded_jwt}")
    return encoded_jwt

def decode_access_token(token: str):
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Decoded JWT Payload: {payload}")
        return payload
    except JWTError:
        logger.error("Invalid JWT Token")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
