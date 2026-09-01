from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000
)

# Check MongoDB connection immediately
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")
except Exception as error:
    print("MongoDB connection failed:", error)
    raise

db = client["UserDB"]

users_collection = db["voice_profiles"]

print("MongoDB connection file loaded successfully!")