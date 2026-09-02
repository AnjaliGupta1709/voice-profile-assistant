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
    tlsVersion="TLSv1.2",
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000
)

db = client["userDB"]

users_collection = db["voice_profiles"]

print("MongoDB client initialized successfully!")
