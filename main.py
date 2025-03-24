from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import motor.motor_asyncio
from typing import List
import base64

app = FastAPI()

# Connect to MongoDB Atlas(replace URI with your actual connection string)
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://Mireya:catdatabase@catgame.ljubd.mongodb.net/?retryWrites=true&w=majority&appName=CatGame"
)
db = client.catgame_db

# Pydantic model for score submissions
class PlayerScore(BaseModel):
    player_name: str
    score: int

# Endpoint to upload sprite images
@app.post("/upload_sprites")
async def upload_sprites(files: List[UploadFile] = File(...)):
    uploaded_ids = []
    try:
        for file in files:
            content = await file.read()
            encoded = base64.b64encode(content).decode("utf-8")
            document = {
                "name": file.filename,
                "content": encoded,
                "content_type": file.content_type
            }
            result = await db.sprites.insert_one(document)
            uploaded_ids.append(str(result.inserted_id))
        return {"message": "Sprites uploaded", "ids": uploaded_ids}
    except Exception as e:
        print("UPLOAD_SPRITES ERROR:", e) 
        return {"error": str(e)}


# Endpoint to upload audio files
@app.post("/upload_audios")
async def upload_audios(files: List[UploadFile] = File(...)):
    uploaded_ids = []
    for file in files:
        content = await file.read()
        encoded = base64.b64encode(content).decode("utf-8")  # Convert to base64 string
        document = {
            "name": file.filename,
            "content": encoded,
            "content_type": file.content_type
        }
        result = await db.audio.insert_one(document)
        uploaded_ids.append(str(result.inserted_id))
    return {"message": "Audios uploaded", "ids": uploaded_ids}

# Endpoint to submit player scores
@app.post("/upload_scores")
async def submit_multiple_scores(scores: List[PlayerScore]):
    results = await db.scores.insert_many([score.dict() for score in scores])
    return {"message": "Multiple scores submitted", "ids": [str(id) for id in results.inserted_ids]}


# Get all sprites
@app.get("/sprites")
async def get_sprites():
    sprites = []
    cursor = db.sprites.find()
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        sprites.append(doc)
    return sprites

# Get all audio files
@app.get("/audios")
async def get_audios():
    audios = []
    cursor = db.audio.find()
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        audios.append(doc)
    return audios

# Get all player scores
@app.get("/scores")
async def get_scores():
    scores = []
    cursor = db.scores.find()
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        scores.append(doc)
    return scores