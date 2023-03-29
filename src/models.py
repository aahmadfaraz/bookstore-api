
from pydantic import BaseModel
from typing import List, Optional, Dict

# Custom user model
class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = False
    author_pseudonym: Optional[str] = None

# Custom book model
class Book(BaseModel):
    id: int
    title: str
    description: str
    author: str
    cover_image: Optional[str] = None
    price: float
    published: bool