import secrets

from config.env_config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def authenticate(
    username: str, password: str, credentials: HTTPBasicCredentials = Depends(security)
):
    """
    Basic authentication dependency function.
    """
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verifies the provided credentials against the API's credentials.
    - Args:
      credentials (HTTPBasicCredentials): The provided credentials.
    - Returns:
        bool: True if the credentials are valid, otherwise False.
    """
    correct_username = credentials.username == settings.api_username
    correct_password = credentials.password == settings.api_password
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
