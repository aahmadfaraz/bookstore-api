from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from json2xml import json2xml
import json

from auth import security
from auth import authenticate_user, create_access_token, get_current_user, verify_password
from models import User, Book
from data import users_db, books_db

# FastAPI App instance
app = FastAPI()

# Middleware
# Middleware to handle Content-Type (xml | json)

async def content_type_middleware(request: Request, call_next):
    response = await call_next(request)
    if "application/xml" in request.headers.get("Content-Type", ""):
        content_type = response.headers.get('content-type')
        # if response is json, convert it to xml
        if 'application/json' in content_type:
            response_body = b""

            async for chunk in response.body_iterator:
                response_body += chunk

            # json_content = Response(content=response_body, 
            #                          status_code=response.status_code, 
            #                          headers=dict(response.headers), 
            #                          media_type=response.media_type)
            
            xml = json2xml.Json2xml(response_body.decode()).to_xml()
            return Response(content=xml, media_type="application/xml")
            
        elif 'text/xml' in content_type:
            # If the response is already XML, just return it as-is
            return response
    return response

app.middleware("http")(content_type_middleware)


# API endpoints
# Login
@app.post("/login")
def login(credentials: HTTPBasicCredentials = Depends(security)) -> Dict[str, str]:
    """
    Authenticate a user with HTTP Basic authentication and create an access token.
    :param credentials: The credentials provided by the client.
    :return: A dictionary containing an access token.
    """
    username = credentials.username
    password = credentials.password

    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
        
    if users_db[username]["active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{username} already Logged In!",
        )
        
    active_users = list(map(lambda user: user['username'], filter(lambda user: user['active'], users_db.values())))
    if len(active_users) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{active_users[0]} is logged In. Logout first!"
        )
    
    for user in users_db.values():
        user['active'] = False
    
    access_token = create_access_token(data={"sub": user["username"]})
    users_db[username]["active"] = True
    return {"access_token": access_token}


# Logout
@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Endpoint to invalidate the current access token and log the user out.
    """

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    if users_db[current_user["username"]]["active"] == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not logged in.",
        )
    
    users_db[current_user["username"]]["active"] = False
    return {"message": "You have been logged out."}



# root/home
@app.get("/")
async def home() -> dict:
    """
    A Home rout which returns a welcome message.
    :return: A dictionary containing a welcome message.
    """
    return {"message": "Welcome to the Bookstore API!"}


# Get a book by Id
@app.get("/books/{book_id}")
def get_book_by_id(book_id: int) -> dict:
    """
    Get a book by ID.
    :param book_id: The ID of the book to retrieve.
    :return: A dictionary containing the book data.
    :raises HTTPException: If the book with the given ID is not found.
    """
    for book in books_db:
        if book["id"] == book_id:
            return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Book not found!")


# Searching books by Title or Author (using query parameter)
# This endpoint provides a robust search functionality for books based on their title or author,
# A flexible way can be to add GraphQL or provide rich query params based on requirements
@app.get("/books")
def get_books_by_search(request: Request):
    query = None
    if "query" in request.query_params:
        query = request.query_params["query"]
    if query:
        search_results = [book for book in books_db if query.lower() in book["title"].lower() or query.lower() in book["author"].lower()]
        if not search_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No books found for query '{query}'.",
            )
        return {"search_results": search_results}
    else:
        return {"books":books_db}


# Create a book
@app.post("/books")
def create_book(book: Book, current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Create a new book in the database.
    :param book: A `Book` instance containing information about the new book.
    :param current_user: A `User` instance representing the currently authenticated user.
    :return: A `JSONResponse` indicating whether the book was created successfully.
    """

    # user not logged in
    if not current_user["active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not logged in.")
    
    # only author can publish
    if current_user["username"] != book.author:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User is not authorized to create book")
    
    # vader is forbidden to publish his books
    if current_user["username"] == "vader":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Darth Vader is not allowed to publish his work on Wookie Books",
        )

    # Check if the book ID already exists
    if any(existing_book["id"] == book.id for existing_book in books_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book ID {book.id} already exists",
        )

    # Add the book to the database
    books_db.append(book.dict())
    return JSONResponse(content={"message": "Book created successfully"}, status_code=status.HTTP_201_CREATED)


# Update a book
@app.put("/books/{book_id}")
def update_book(book_id: int, book_to_update: Book, current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Update a book with the given book_id in the books database.
    Args:
        book_id (int): The id of the book to be updated.
        book_to_update (Book): The updated book information.
        current_user (User, optional): The current user. Defaults to Depends(get_current_user).
    Returns:
        JSONResponse: A JSON response indicating if the book was updated successfully or not.
    """
    for i, book in enumerate(books_db):
        if book["id"] == book_id:
            if current_user["username"] != book["author"]:
                raise HTTPException(
                    status_code=401, detail="User is not authorized to update book")
            for b in books_db:
                if b["id"] == book_to_update.id and b is not book:
                    raise HTTPException(
                        status_code=409, detail=f"Book ID {update_book.id} already exists in database")
            books_db[i] = book_to_update.dict()
            return JSONResponse(content={"message": "Book updated successfully"}, status_code=status.HTTP_200_OK)
    raise HTTPException(status_code=404, detail="Book not found")



# Delete a book
@app.delete("/books/{book_id}")
def delete_book(book_id: int, current_user: User = Depends(get_current_user)):
    """
    Deletes a book with the given ID and returns the deleted book.
    Args:
        book_id (int): The ID of the book to delete.
        current_user (User): The current authenticated user.
    Returns:
        dict: The deleted book.
    Raises:
        HTTPException: If the book is not found or the user is not authorized.
    """

    book_index = None
    for i, book in enumerate(books_db):
        if book["id"] == book_id:
            book_index = i
            break

    if book_index is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if current_user["username"] != books_db[book_index]["author"]:
        raise HTTPException(status_code=403, detail="User is not authorized to delete book")

    deleted_book = books_db.pop(book_index)
    return JSONResponse(content={"message": "Book deleted successfully"}, status_code=status.HTTP_200_OK)
    # return deleted_book


def main():
    import uvicorn
    # run server
    uvicorn.run("build:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
