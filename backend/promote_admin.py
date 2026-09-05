from pymongo import MongoClient

# Run this one-off script only after creating the target account through the API.
client = MongoClient("mongodb://localhost:27017")
db = client["rag_chatbot"]
result = db.users.update_one({"email": "admin@test.com"}, {"$set": {"role": "admin"}})
print("Matched:", result.matched_count, "Modified:", result.modified_count)