# config.py
# This module loads environment variables from the .env file
# and makes them available as Python variables.

import os
from dotenv import load_dotenv

# Load environment variables from the .env file located in the project root
# find_dotenv() helps locate the .env file automatically
# load_dotenv(find_dotenv()) # Alternative if .env isn't in the same dir as script execution
load_dotenv()

# Retrieve the Google API Key from the environment variables
# os.getenv() returns None if the variable is not found, which is safer
# than os.environ[] which would raise an error.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# You could add other configurations here as needed,
# for example, database file path:
# DATABASE_NAME = os.getenv("DATABASE_NAME", "game.db") # With default value

# Optional: Add a check to ensure the API key was loaded
if GOOGLE_API_KEY is None:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")
    # Depending on your application, you might want to raise an error here
    # raise ValueError("GOOGLE_API_KEY not set. Please check your .env file.")
