from fastapi.testclient import TestClient
import sys
import os

# Add the path of the directory containing build.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import modules
from build import app
from data import users_db, books_db
from models import User, Book


client = TestClient(app)

# TEST LOGIN ENDPOINT
# test 1
def test_successful_login():
    response = client.post("/login", auth=("wookie1", "wookie1@123"))
    assert response.status_code == 200
    assert "access_token" in response.json()
    client.post("/logout", auth=("wookie1", "wookie1@123"))

# test 2
def test_login_with_invalid_credentials():
    response = client.post("/login", auth=("user", "user123"))
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Basic"
    assert response.json()["detail"] == "Invalid username or password"

# test 3
def test_login_with_already_logged_in_user():
    # login
    client.post("/login", auth=("wookie1", "wookie1@123"))
    # trying to login again
    response = client.post("/login", auth=("wookie1", "wookie1@123"))
    assert response.status_code == 401
    assert "already Logged In!" in response.json()["detail"]
    client.post("/logout", auth=("wookie1", "wookie1@123"))


# TEST LOGOUT ENDPOINT
# test 1
def test_successful_logout():
    # Login user first
    client.post("/login", auth=("wookie1", "wookie1@123"))
    response = client.post("/logout", auth=("wookie1", "wookie1@123"))
    assert response.status_code == 200
    assert response.json()["message"] == "You have been logged out."

# test 2
def test_logout_with_user_not_logged_in():
    response = client.post("/logout", auth=("wookie2", "wookie2@123"))
    assert response.status_code == 401

# TEST HOME ENDPOINT (welcome msg)
def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Bookstore API!"}


# TEST GET BOOKS ENDPOINT
# test 1 (get all books)
def test_get_all_books():
    response = client.get("/books")
    assert response.status_code == 200
    assert len(response.json()["books"]) == 3

# TEST GET BOOK BY ID ENDPOINT
# test 1
def test_get_book_by_id():
    book_id = 1
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "The Big Adventure"

# test 2
def test_get_book_by_id_not_found():
    book_id = 100
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found!"


# TEST BOOKS BY SEARCH ENDPOING (Query Param)
# test 1
def test_get_books_by_search():
    response = client.get("/books?query=big")
    assert response.status_code == 200
    assert len(response.json()["search_results"]) == 1
    assert response.json()["search_results"][0]["title"] == "The Big Adventure"

# test 2
def test_get_books_by_search_not_found():
    response = client.get("/books?query=xyz")
    assert response.status_code == 404
    assert response.json()["detail"] == "No books found for query 'xyz'."


# TEST CREATE BOOK ENDPOINT
# test 1 
def test_create_book_successfully():
    new_book = {
        "id": 45,
        "title": "Python Handbook",
        "description": "Learn Python the best way!",
        "author": "wookie2",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 6.54,
        "published": True
    }
    client.post("/login", auth=("wookie2", "wookie2@123"))
    response = client.post("/books", json=new_book, auth=("wookie2", "wookie2@123"))
    assert response.status_code == 201
    assert response.json() == {"message": "Book created successfully"}
    assert new_book in books_db
    del books_db[-1]
    client.post("/logout", auth=("wookie2", "wookie2@123"))

# test 2
def test_create_book_unauthorized():
    new_book = {
        "id": 5,
        "title": "Python Handbook",
        "description": "Learn Python the best way!",
        "author": "wookie2",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 6.54,
        "published": True
    }
    client.post("/login", auth=("wookie1", "wookie1@123"))
    response = client.post("/books", json=new_book, auth=("wookie1", "wookie1@123"))
    assert response.status_code == 403
    assert response.json()["detail"] == "User is not authorized to create book"
    assert new_book not in books_db
    client.post("/logout", auth=("wookie1", "wookie1@123"))

# test 3
def test_create_book_forbidden():
    new_book = {
        "id": 5,
        "title": "Python Handbook",
        "description": "Learn Python the best way!",
        "author": "vader",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 6.54,
        "published": True
    }
    client.post("/login", auth=("vader", "vader@123"))
    response = client.post("/books", json=new_book, auth=("vader", "vader@123"))
    assert response.status_code == 403
    assert response.json()["detail"] == "Darth Vader is not allowed to publish his work on Wookie Books"
    assert new_book not in books_db
    client.post("/logout", auth=("vader", "vader@123"))

# test 4
def test_create_book_bad_request():
    new_book = {
        "id": 1,
        "title": "Python Handbook",
        "description": "Learn Python the best way!",
        "author": "wookie1",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 6.54,
        "published": True
    }
    client.post("/login", auth=("wookie1", "wookie1@123"))
    response = client.post("/books", json=new_book, auth=("wookie1", "wookie1@123"))
    assert response.status_code == 400
    assert response.json()["detail"] == "Book ID 1 already exists"
    print("bookssss",books_db,flush=True)
    assert len(books_db) == 3
    client.post("/logout", auth=("wookie1", "wookie1@123"))


# TEST UPDATE ENDPOINT
# test 1
def test_update_book_successfully():
    book_to_update_id = 2

    # update the book
    updated_data = {
        "id": 1000,
        "title": "Python Handbook",
        "description": "Learn Python the best way!",
        "author": "wookie2",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 6.54,
        "published": True
    }
    response = client.put(f"/books/{book_to_update_id}", json=updated_data, auth=("wookie2", "wookie2@123"))
    assert response.status_code == 200
    assert response.json() == {"message": "Book updated successfully"}

# test 2
def test_update_book_not_found():
    book_to_update_id = 55

    # update the book
    updated_data = {
        "id": 5,
        "title": "Python Handbook",
        "description": "Learn Python the best way!",
        "author": "wookie2",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 6.54,
        "published": True
    }
    response = client.put(f"/books/{book_to_update_id}", json=updated_data, auth=("wookie2", "wookie2@123"))
    assert response.status_code == 404
    assert response.json() == {"detail":"Book not found"}
    client.post("/logout", auth=("wookie2", "wookie2@123"))

# test 3
def test_update_book_not_authorized():
    # create test book
    data = {
        "id": 20,
        "title": "The Epic Journey",
        "description": "An epic journey through the stars",
        "author": "wookie2",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 8.99,
        "published": True
    }
    # login as wookie2
    response = client.post("/login", auth=("wookie2", "wookie2@123"))
    assert response.status_code == 200
    # create book with wookie2
    response = client.post("/books", json=data, auth=("wookie2", "wookie2@123"))
    print("11111",response.json())
    assert response.status_code == 201
    # logout wookie2
    response = client.post("/logout", auth=("wookie2", "wookie2@123"))
    assert response.status_code == 200
    # login as wookie1
    response = client.post("/login", auth=("wookie1", "wookie1@123"))
    print("22222",response.json())
    assert response.status_code == 200
    # attempt to update book with wookie1 (should fail)
    response = client.put("/books/20", json=data, auth=("wookie1", "wookie1@123"))
    assert response.status_code == 401
    assert response.json() == {"detail": "User is not authorized to update book"}



# TEST DELETE ENTPOINT
def test_delete_book():
    # test deleting a book that exists in the database
    response = client.delete("/books/1",auth=("wookie1", "wookie1@123"))
    assert response.status_code == 200
    assert response.json() == {"message": "Book deleted successfully"}

    # test deleting a book that does not exist in the database
    response = client.delete("/books/123",auth=("wookie2", "wookie2@123"))
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}

    # test deleting a book with an invalid book ID
    response = client.delete("/books/invalid_id",auth=("wookie2", "wookie2@123"))
    assert response.status_code == 422
    assert response.json() == {"detail": [{"loc": ["path", "book_id"], "msg": "value is not a valid integer", "type": "type_error.integer"}]}

    # test deleting a book without authentication
    response = client.delete("/books/2")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # test deleting a book as a non-author user
    response = client.delete("/books/3", auth=("vader", "vader@123"))
    assert response.status_code == 403
    assert response.json() == {"detail": "User is not authorized to delete book"}