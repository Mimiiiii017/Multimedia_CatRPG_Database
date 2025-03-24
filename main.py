from http.client import HTTPException
from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import motor.motor_asyncio
from typing import List
import base64 # Used to encode binary data into base64 strings

app = FastAPI()

# Connect to MongoDB Atlas(replace URI with your actual connection string)
# This connects to the cloud MongoDB database where sprites, audios, and scores will be stored
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://Mireya:catdatabase@catgame.ljubd.mongodb.net/?retryWrites=true&w=majority&appName=CatGame"
)
db = client.catgame_db

# Pydantic model for score submissions
# This ensures any JSON input for scores follows this structure:
# {
#   "player_name": "Alice",
#   "score": 1234
# }
class PlayerScore(BaseModel):
    player_name: str
    score: int

# Endpoint to upload sprite images
    ## Upload multiple sprite images to the database.
    ## Each file is:
    ##  - Read asynchronously
    ##  - Encoded in base64 format
    ##  - Stored in the 'sprites' collection with metadata
    ## Returns a list of inserted document IDs.
@app.post("/upload_sprites")
async def upload_sprites(files: List[UploadFile] = File(...)):
    
    uploaded_ids = [] # Will hold MongoDB document IDs
    try:
        for file in files:
            content = await file.read() # Read the binary content of the file
            encoded = base64.b64encode(content).decode("utf-8") # Convert to base64 string
            # Create a document to store
            document = {
                "name": file.filename,
                "content": encoded,
                "content_type": file.content_type
            }
             # Insert the document into the 'sprites' collection
            result = await db.sprites.insert_one(document)
            uploaded_ids.append(str(result.inserted_id))  # Store the ID of the inserted doc
        return {"message": "Sprites uploaded", "ids": uploaded_ids}
    except Exception as e:
        # If something goes wrong, print and return the error
        print("UPLOAD_SPRITES ERROR:", e) 
        return {"error": str(e)}


# Endpoint to upload audio files
    ## Upload multiple audio files to the database.
    ## Each file is base64 encoded and saved to the 'audio' collection.

    ## Returns a list of inserted document IDs.
@app.post("/upload_audios")
async def upload_audios(files: List[UploadFile] = File(...)):
    uploaded_ids = []
    for file in files:
        content = await file.read() # Read file as binary
        encoded = base64.b64encode(content).decode("utf-8")  # Convert to base64 string
        document = {
            "name": file.filename,
            "content": encoded,
            "content_type": file.content_type
        }
        result = await db.audio.insert_one(document)
        uploaded_ids.append(str(result.inserted_id)) # Store the ID of the inserted doc
    return {"message": "Audios uploaded", "ids": uploaded_ids}


# Endpoint to submit player scores
# Accepts a list of player scores in JSON format and stores them in the 'scores' collection.
@app.post("/upload_scores")
# Convert Pydantic models to dicts and insert all at once
async def submit_multiple_scores(scores: List[PlayerScore]):
    clean_scores = []
    for score in scores:
        if not score.player_name.isalnum():  # Reject suspicious names like "$ne"
            raise HTTPException(status_code=400, detail="Invalid player name.")
        clean_scores.append(score.dict())
    
    results = await db.scores.insert_many(clean_scores)
    return {"message": "Multiple scores submitted", "ids": [str(id) for id in results.inserted_ids]}




# Get all sprites
# Retrieves all sprite documents from the database.
@app.get("/sprites")
async def get_sprites():
    sprites = []
    cursor = db.sprites.find() # Get all documents in 'sprites'
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        sprites.append(doc)
    return sprites

# Get all audio files
# Retrieves all audio documents from the database.
@app.get("/audios")
async def get_audios():
    audios = []
    cursor = db.audio.find()
    async for doc in cursor:
        doc["_id"] = str(doc["_id"]) # Convert ObjectId for frontend use
        audios.append(doc)
    return audios

# Get all player scores
# Retrieves all player scores from the 'scores' collection.
@app.get("/scores")
async def get_scores():
    scores = []
    cursor = db.scores.find()
    async for doc in cursor:
        doc["_id"] = str(doc["_id"]) # Convert ObjectId
        scores.append(doc)
    return scores