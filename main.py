from fastapi import FastAPI, File, UploadFile, Form
from typing import List
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import motor.motor_asyncio
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
    for file in files:
        content = await file.read()
        encoded = base64.b64encode(content).decode("utf-8")  # Convert to base64 string
        document = {
            "name": file.filename,
            "content": encoded,
            "content_type": file.content_type
        }
        result = await db.sprites.insert_one(document)
        uploaded_ids.append(str(result.inserted_id))
    return {"message": "Sprites uploaded", "ids": uploaded_ids}


# Endpoint to upload audio files
@app.post("/upload_sprites")
async def upload_sprites(files: List[UploadFile] = File(..., media_type="multipart/form-data")):
    uploaded_ids = []
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

# Endpoint to submit player scores
@app.post("/upload_scores")
async def submit_multiple_scores(scores: List[PlayerScore]):
    results = await db.scores.insert_many([score.dict() for score in scores])
    return {"message": "Multiple scores submitted", "ids": [str(id) for id in results.inserted_ids]}