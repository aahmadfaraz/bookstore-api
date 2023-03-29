# Bookstore API

The implementation uses Python programming language and the FastAPI framework.

The API supports returning data in JSON or XML format based on the Content-Type header. There is also an endpoint for user authentication using a username and password. An access token is returned to authenticated users to access protected routes/operations.

# Installation

1. Clone this repository: git clone https://github.com/your-username/bookstore-api.git
2. Change directory into the project folder: cd bookstore-api
3. Install the required packages: pip install -r requirements.txt
4. Run the application: python3 build.py


# API Endpoints
## Authentication
#### POST /login
This endpoint requires a username and password in the request body and returns an access token after successful user authentication.

#### POST /logout
This endpoint logs out a logged in user

## Books
#### GET /books
This endpoint returns a list of all published books. Also returns filtered books based on search query (if provided).

#### Get /books/{book_id}
This endpoint retrieves a specific book by id.

#### POST /books
This endpoint allows authenticated users to publish a new book.

#### PUT /books/{book_id}
This endpoint allows authenticated users to update their own published books.

#### DELETE /books/{book_id}
This endpoint allows authenticated users to unpublish / delete their own books.


## Try it here:
https://placely-test-dep-production.up.railway.app/docs