from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.hash import pbkdf2_sha256
import jwt

from data import users_db, books_db
from models import User, Book
from app_constants import SECRET_KEY, ALGORITHM

# FastAPI App instance
app = FastAPI()

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
    if username in users_db:
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

# Dependency to get current user
def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> Optional[User]:
    """
    Get the current authenticated user.
    :param credentials: The credentials provided by the client.
    :return: The authenticated user object, or rais HTTPException if authentication fails.
    """
    username = credentials.username
    password = credentials.password
    user = authenticate_user(username, password)
    if not user:
        return None
    return user