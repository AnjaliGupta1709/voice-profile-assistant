import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set")

client = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
)

db = client["UserDB"]

users_collection = db["voice_profiles"]

print("MongoDB client initialized successfully!")