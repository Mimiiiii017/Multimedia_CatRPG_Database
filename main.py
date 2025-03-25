from http.client import HTTPException # Used for raising HTTP error responses
from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, UploadFile, Depends # Core FastAPI modules
from pydantic import BaseModel # For input validation using data models
import motor.motor_asyncio # Async MongoDB driver
from typing import List
import base64 # Used to encode binary data into base64 strings

# Initialize the FastAPI app
app = FastAPI()

# Database connection setup
# This function creates a fresh connection to MongoDB Atlas each time it's called.
# It's used with FastAPI's 'Depends' feature to avoid connection timeout issues on Vercel.
async def get_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        "mongodb+srv://Mireya:catdatabase@catgame.ljubd.mongodb.net/?retryWrites=true&w=majority&appName=CatGame"
    )
    return client.catgame_db

# Define the expected format for player scores using Pydantic.
# This ensures incoming POST data is validated for structure and type.
class PlayerScore(BaseModel): 
    player_name: str # Must be a string (e.g., "Alice")
    score: int # Must be an integer (e.g., 4000)


# ----------------------------- UPLOAD ROUTES -----------------------------


# Upload one or more sprite images.
# Each file is read as binary, encoded to base64, and stored in MongoDB with metadata.
@app.post("/upload_sprites")
async def upload_sprites(files: List[UploadFile] = File(...), db=Depends(get_db)):
    uploaded_ids = [] # Will store MongoDB document IDs of inserted sprites
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


# Upload one or more audio files (e.g., MP3s).
# Audio is stored in base64 format in the 'audio' collection.
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


# Upload one or more player scores in JSON format.
# Example:
# [
#   { "player_name": "Alice", "score": 3000 },
#   { "player_name": "Bob", "score": 4500 }
# ]
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


# Retrieve all sprite records from MongoDB.
# Returns a list of image names and base64 content.
@app.get("/sprites")
async def get_sprites(db=Depends(get_db)):
    sprites = []
    cursor = db.sprites.find() # Query all documents in the 'sprites' collection
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string so it can be serialized in JSON
        sprites.append(doc)
    return sprites


# Retrieve all uploaded audio files.
# Each entry contains the filename, content type, and base64 audio data.
@app.get("/audios")
async def get_audios(db=Depends(get_db)):
    audios = []
    cursor = db.audio.find() # Query all documents in the 'audios' collection
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string so it can be serialized in JSON
        audios.append(doc)
    return audios

# Retrieve all player scores.
# Returns each score with player name and score value.
@app.get("/scores")
async def get_scores(db=Depends(get_db)):
    scores = []
    cursor = db.scores.find() # Query all documents in the 'scores' collection
    async for doc in cursor:
        doc["_id"] = str(doc["_id"]) # Convert ObjectId
        scores.append(doc)
    return scores