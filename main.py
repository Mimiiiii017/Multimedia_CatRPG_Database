from fastapi import HTTPException # Used for raising HTTP error responses
import os 
from fastapi.responses import JSONResponse # Allows custom response formatting (not directly used here)
from fastapi import FastAPI, File, UploadFile, Depends # Core FastAPI modules
from pydantic import BaseModel # For input validation using data models
import motor.motor_asyncio # Async MongoDB client for interacting with MongoDB Atlas
from typing import List  # Allows defining endpoints that accept a list of inputs
import base64 # Used to convert binary files to base64 strings for safe storage in MongoDB
from dotenv import load_dotenv
from bson import ObjectId

# Initialize the FastAPI app
app = FastAPI()

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")  # Explicit path

# Function: Sanitize score update data
# Purpose: Prevent NoSQL injection by rejecting keys or values with dangerous characters like $, {, or .
def sanitize_score_update(data: dict) -> dict:
    for key in data:
        if "$" in key or "." in key:
            return None  # Reject dangerous field names
        value = data[key]
        if isinstance(value, str) and ("$" in value or "{" in value or "}" in value):
            return None  # Reject suspicious string values
    return data  # Return sanitized data if clean


# ----------------------------- MONGO DB CONNECTION -----------------------------


# Use environment variable for MongoDB connection string
MONGODB_URL = os.getenv("MONGODB_URL")
print("DEBUG MONGODB_URL:", MONGODB_URL)


# Dependency function to connect to MongoDB using secure .env config
async def get_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    return client.catgame_db

# Define the expected format for player scores using Pydantic.
# This ensures incoming POST data is validated for structure and type.
class PlayerScore(BaseModel): 
    player_name: str # Must be a string (e.g., "Alice")
    score: int # Must be an integer (e.g., 4000)


# ----------------------------- UPLOAD ROUTES -----------------------------


# Endpoint: Upload one or more sprite images
# Method: POST
# Route: /upload_sprites
# Accepts multiple image files via form-data, encodes them in base64, and stores them in MongoDB
@app.post("/upload_sprites")
async def upload_sprites(files: List[UploadFile] = File(...), db=Depends(get_db)):
    uploaded_ids = [] # Store MongoDB document IDs of inserted sprites
    try:
        for file in files:
            content = await file.read() # Read file content asynchronously
            encoded = base64.b64encode(content).decode("utf-8") # Convert to base64 string
            # Create a document to store
            document = {
                "name": file.filename,
                "content": encoded,
                "content_type": file.content_type # e.g., image/png
            }
             # Insert the document into the 'sprites' collection in MongoDB
            result = await db.sprites.insert_one(document)
            uploaded_ids.append(str(result.inserted_id))  # Store the generated ObjectId
        return {"message": "Sprites uploaded", "ids": uploaded_ids}
    except Exception as e:
        # If something goes wrong, print and return the error
        print("UPLOAD_SPRITES ERROR:", e) 
        return {"error": str(e)}


# Endpoint: Upload one or more audio files
# Method: POST
# Route: /upload_audios
# Encodes MP3 files in base64 and stores them in MongoDB
@app.post("/upload_audios")
async def upload_audios(files: List[UploadFile] = File(...), db=Depends(get_db)):
    uploaded_ids = []
    for file in files:
        content = await file.read() # Read file content asynchronously
        encoded = base64.b64encode(content).decode("utf-8")  # Convert to base64 string
        document = {
            "name": file.filename,
            "content": encoded,
            "content_type": file.content_type # e.g., audio/mpeg
        }
        result = await db.audio.insert_one(document)
        uploaded_ids.append(str(result.inserted_id)) # Store the ID of the inserted doc
    return {"message": "Audios uploaded", "ids": uploaded_ids}


# Endpoint: Upload multiple player scores
# Method: POST
# Route: /upload_scores
# Accepts a list of JSON objects like: [{"player_name": "Alice", "score": 5000}, ...]
# Validates and inserts them into the 'scores' collection
@app.post("/upload_scores")
async def submit_multiple_scores(scores: List[PlayerScore], db=Depends(get_db)):
    # Basic sanitization: prevent NoSQL injection by disallowing special characters
    clean_scores = []
    for score in scores:
        if not score.player_name.isalnum():  # Reject suspicious names like "$ne"
            raise HTTPException(status_code=400, detail="Invalid player name.")
        clean_scores.append(score.dict())
    
    # Insert all valid scores into the 'scores' collection
    results = await db.scores.insert_many(clean_scores)
    return {"message": "Multiple scores submitted", "ids": [str(id) for id in results.inserted_ids]}


# ----------------------------- RETRIEVAL ROUTES -----------------------------


# Endpoint: Retrieve all sprite images
# Method: GET
# Route: /sprites
# Returns a list of documents containing name, content (base64), and content_type
@app.get("/sprites")
async def get_sprites(db=Depends(get_db)):
    sprites = []
    cursor = db.sprites.find() # Query all documents in the 'sprites' collection
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string so it can be serialized in JSON
        sprites.append(doc)
    return sprites


# Endpoint: Retrieve all audio files
# Method: GET
# Route: /audios
# Returns list of audio records with base64-encoded data
@app.get("/audios")
async def get_audios(db=Depends(get_db)):
    audios = []
    cursor = db.audio.find() # Query all documents in the 'audios' collection
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string so it can be serialized in JSON
        audios.append(doc)
    return audios

# Endpoint: Retrieve all player scores
# Method: GET
# Route: /scores
# Returns documents with player_name and score values
@app.get("/scores")
async def get_scores(db=Depends(get_db)):
    scores = []
    cursor = db.scores.find() # Query all documents in the 'scores' collection
    async for doc in cursor:
        doc["_id"] = str(doc["_id"]) # Convert ObjectId
        scores.append(doc)
    return scores



# ----------------------------- UPDATE ROUTES -----------------------------


# Endpoint: Update a specific sprite document by ID
# Method: PUT
# Route: /sprites/{sprite_id}
# Accepts JSON with updated fields (e.g., name, content), and updates the sprite in MongoDB
@app.put("/sprites/{sprite_id}")
async def update_sprite(sprite_id: str, updated_data: dict, db=Depends(get_db)):
    await db.sprites.update_one({"_id": ObjectId(sprite_id)}, {"$set": updated_data})
    return {"message": "Sprite updated"}

# Endpoint: Update a specific audio document by ID
# Method: PUT
# Route: /audios/{audio_id}
# Accepts JSON with updated fields (e.g., name, content), and updates the audio in MongoDB
@app.put("/audios/{audio_id}")
async def update_audio(audio_id: str, updated_data: dict, db=Depends(get_db)):
    await db.audio.update_one({"_id": ObjectId(audio_id)}, {"$set": updated_data})
    return {"message": "Audio updated"}

# Endpoint: Update a specific score document by ID
# Method: PUT
# Route: /scores/{score_id}
# Accepts JSON with fields like player_name and score. Sanitizes input before updating.
@app.put("/scores/{score_id}")
async def update_score(score_id: str, updated_data: dict, db=Depends(get_db)):
    sanitized = sanitize_score_update(updated_data)
    if sanitized is None:
        return {"message": "Invalid or unsafe data"}
    await db.scores.update_one({"_id": ObjectId(score_id)}, {"$set": sanitized})
    return {"message": "Score updated"}


# ----------------------------- DELETE ROUTES -----------------------------


# Endpoint: Delete a specific sprite document by ID
# Method: DELETE
# Route: /sprites/{sprite_id}
# Deletes the sprite from the 'sprites' collection
@app.delete("/sprites/{sprite_id}")
async def delete_sprite(sprite_id: str, db=Depends(get_db)):
    await db.sprites.delete_one({"_id": ObjectId(sprite_id)})
    return {"message": "Sprite deleted"}

# Endpoint: Delete a specific audio document by ID
# Method: DELETE
# Route: /audios/{audio_id}
# Deletes the audio file from the 'audio' collection
@app.delete("/audios/{audio_id}")
async def delete_audio(audio_id: str, db=Depends(get_db)):
    await db.audio.delete_one({"_id": ObjectId(audio_id)})
    return {"message": "Audio deleted"}

# Endpoint: Delete a specific score document by ID
# Method: DELETE
# Route: /scores/{score_id}
# Deletes the score record from the 'scores' collection
@app.delete("/scores/{score_id}")
async def delete_score(score_id: str, db=Depends(get_db)):
    await db.scores.delete_one({"_id": ObjectId(score_id)})
    return {"message": "Score deleted"}


# ----------------------------- TESTS TO CHECK MY CONNECTION -----------------------------


@app.get("/")
def root():
    return {"message": "FastAPI is running on Vercel!"}


@app.get("/ping")
async def ping(db=Depends(get_db)):
    try:
        await db.command("ping")
        return {"message": "Connected to MongoDB!"}
    except Exception as e:
        return {"error": str(e)}
