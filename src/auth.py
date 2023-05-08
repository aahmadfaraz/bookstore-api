from typing import Any, List, Optional, Dict, Union
from fastapi import FastAPI, HTTPException, Header, status, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.hash import pbkdf2_sha256
import jwt
from jwt.exceptions import InvalidSignatureError, DecodeError

from data import users_db, books_db
from models import User, Book
from app_constants import SECRET_KEY, ALGORITHM

# Security
security = HTTPBasic()

# Function to verify password hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that the plain text password matches the hashed password.
    Returns:
        bool: True if the plain text password matches the hashed password, False otherwise.
    """
    return pbkdf2_sha256.verify(plain_password, hashed_password)


# Function to authenticate user
def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticates a user by checking if the username exists in the users database,
    and if the provided password matches the hashed password for the user.
    Returns:
        Optional[User]: The User object if authentication is successful, None otherwise.
    """
    if username not in users_db:
        return None

    user = users_db[username]
    hashed_password = pbkdf2_sha256.hash(user["password"])
    if verify_password(password, hashed_password):
        return user
    else:
        return None


# Function to create access token
def create_access_token(data: dict):
    """
    Create an access token using the provided user data, secret key, and algorithm.
    """
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# returns user if found in DB or else none
def get_user(username: str) -> Optional[User]:
    
    if username not in users_db:
        return None
    return users_db[username]


# Dependency to get current user
async def get_current_user(authorization: str = Header(...)) -> Optional[User]:
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
    except (HTTPException, InvalidSignatureError, DecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
