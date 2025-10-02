from config.env_config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

# Create API key header scheme
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key_header: str = Depends(api_key_scheme)):
    """
    Verify the API key from the X-API-Key header.

    Args:
        api_key_header (str): The API key from the X-API-Key header.

    Returns:
        str: The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    if api_key_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key_header != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key_header


# Export the dependency for convenient reuse
api_key_dependency = Depends(verify_api_key)
