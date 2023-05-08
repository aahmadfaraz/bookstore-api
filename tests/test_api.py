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
    # login
    response = client.post("/login", auth=("wookie1", "wookie1@123"))
    assert response.status_code == 200
    assert "access_token" in response.json()
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # logout
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/logout", headers=headers)


# test 2
def test_login_with_invalid_credentials():
    response = client.post("/login", auth=("user", "user123"))
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Basic"
    assert response.json()["detail"] == "Invalid username or password"

# test 3
def test_login_with_already_logged_in_user():
    # login
    first_login_response = client.post("/login", auth=("wookie1", "wookie1@123"))
    token = first_login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # trying to login again
    second_login_response = client.post("/login", auth=("wookie1", "wookie1@123"))
    assert second_login_response.status_code == 401
    assert "already Logged In!" in second_login_response.json()["detail"]
    
    # logout
    client.post("/logout", headers=headers)


# TEST LOGOUT ENDPOINT
# test 1
def test_successful_logout():
    # login
    response = client.post("/login", auth=("wookie1", "wookie1@123"))
    assert response.status_code == 200
    token = response.json()["access_token"]

    # logout
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "You have been logged out."


# test 2
def test_logout_with_wrong_credentials():
    # login
    response = client.post("/login", auth=("wookie1", "wookie1@123"))
    valid_token = response.json()["access_token"]
    dummy_token = "DummyBearerToken"

    # logout with dummy token
    headers = {"Authorization": f"Bearer {dummy_token}"}
    response = client.post("/logout", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"

    # logout
    headers = {"Authorization": f"Bearer {valid_token}"}
    client.post("/logout", headers=headers)


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
    query="big"
    response = client.get(f"/books?query={query}")
    assert response.status_code == 200
    assert len(response.json()["search_results"]) == 1

# test 2
def test_get_books_by_search_not_found():
    query="xyz"
    response = client.get(f"/books?query={query}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"No books found for query '{query}'."


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
    # login & get token
    login_response = client.post("/login", auth=("wookie2", "wookie2@123"))
    token = login_response.json()["access_token"]
    # create book
    headers = {"Authorization": f"Bearer {token}"}
    create_book_response = client.post("/books", json=new_book, headers=headers)
    assert create_book_response.status_code == 201
    assert create_book_response.json() == {"message": "Book created successfully"}
    assert new_book in books_db
    del books_db[-1]
    
    # logout
    client.post("/logout", headers=headers)

# test 2
def test_create_book_unauthorized():
    new_book = {
        "id": 5,
        "title": "Python Handbook",
        "description": "Learn Python the best way!",
        "author": "wookie1",
        "cover_image": "https://loremflickr.com/320/240",
        "price": 6.54,
        "published": True
    }
    # login
    login_response = client.post("/login", auth=("wookie2", "wookie2@123"))
    token = login_response.json()["access_token"]
    # create
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/books", json=new_book, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "User is not authorized to create book"
    assert new_book not in books_db

    # logout
    client.post("/logout", headers=headers)

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
    # login
    login_response = client.post("/login", auth=("vader", "vader@123"))
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # create
    create_response = client.post("/books", json=new_book, headers=headers)
    assert create_response.status_code == 403
    assert create_response.json()["detail"] == "Darth Vader is not allowed to publish his work on Wookie Books"
    assert new_book not in books_db
    # logout
    client.post("/logout", headers=headers)

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
    # login
    login_response = client.post("/login", auth=("wookie1", "wookie1@123"))
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # create
    create_response = client.post("/books", json=new_book, headers=headers)
    assert create_response.status_code == 400
    assert create_response.json()["detail"] == "Book ID 1 already exists"
    assert len(books_db) == 3
    # logout
    client.post("/logout", headers=headers)


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
    # login
    login_response = client.post("/login", auth=("wookie2", "wookie2@123"))
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # update
    response = client.put(f"/books/{book_to_update_id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Book updated successfully"}
    # logout
    client.post("/logout", headers=headers)

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
    # login
    login_response = client.post("/login", auth=("wookie2", "wookie2@123"))
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # update
    response = client.put(f"/books/{book_to_update_id}", json=updated_data, headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail":"Book not found"}
    # logout
    client.post("/logout", headers=headers)

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
    # login
    login_one_response = client.post("/login", auth=("wookie2", "wookie2@123"))
    login_one_token = login_one_response.json()["access_token"]
    login_one_headers = {"Authorization": f"Bearer {login_one_token}"}
    # create
    client.post("/books", json=data, headers=login_one_headers)
    # logout wookie2
    client.post("/logout", headers=login_one_headers)
    # login as wookie1
    login_two_response = client.post("/login", auth=("wookie1", "wookie1@123"))
    login_two_token = login_two_response.json()["access_token"]
    login_two_headers = {"Authorization": f"Bearer {login_two_token}"}
    # attempt to update book with wookie1
    update_response = client.put("/books/20", json=data, headers=login_two_headers)
    assert update_response.status_code == 401
    assert update_response.json() == {"detail": "User is not authorized to update book"}

    # logout
    client.post("/logout", headers=login_two_headers)



# TEST DELETE ENTPOINT
def test_delete_book():

    # login
    login_response = client.post("/login", auth=("wookie1", "wookie1@123"))
    login_token = login_response.json()["access_token"]
    login_headers = {"Authorization": f"Bearer {login_token}"}

    # test deleting a book that exists in the database
    response = client.delete("/books/1",headers=login_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Book deleted successfully"}

    # test deleting a book that does not exist in the database
    response = client.delete("/books/123",headers=login_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}

    # test deleting a book with an invalid book ID
    response = client.delete("/books/invalid_id",headers=login_headers)
    assert response.status_code == 422

    # test deleting a book as a non-author user
    response = client.delete("/books/20", headers=login_headers)
    assert response.status_code == 403
    assert response.json() == {"detail": "User is not authorized to delete book"}