from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# JWT token secret
# Get the value of the SECRET_KEY variable
SECRET_KEY = os.getenv("SECRET_KEY")

# Algorithm
ALGORITHM = "HS256"