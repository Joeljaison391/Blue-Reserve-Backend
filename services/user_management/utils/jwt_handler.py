import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

# Initialize Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# JWT Configurations
SECRET_KEY = os.getenv("JWT_SECRET", "your_secret_key")  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Security Schema
security = HTTPBearer()

def decode_access_token(token: str):
    """
    Decode and validate a JWT token.
    :param token: JWT Token string
    :return: Decoded user information (dict)
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Extract JWT token from Authorization header and decode it.
    :param credentials: HTTPBearer Authorization Header
    :return: Decoded user information (dict)
    """
    token = credentials.credentials
    logger.debug(f"Received Token: {token}")

    user_data = decode_access_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")

    logger.debug(f"Decoded User Data: {user_data}")
    return user_data
