import os

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from utilities import envs

API_KEY = os.getenv("API_KEY", "123456789")

api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=True)


def authenticate(api_key: str = Depends(api_key_scheme)):
    if api_key == API_KEY:
        return True
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
