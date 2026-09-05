import os

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "rag_chatbot")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Keep collection handles in one place so route modules share the same database.
users_col = db["users"]
feedback_col = db["feedback"]
tickets_col = db["tickets"]

users_col.create_index("email", unique=True)
tickets_col.create_index("employee_id")
tickets_col.create_index("status")
tickets_col.create_index([("created_at", DESCENDING)])

feedback_col.create_index("session_id")
feedback_col.create_index("rating")
feedback_col.create_index("was_escalated")
feedback_col.create_index([("submitted_at", DESCENDING)])
