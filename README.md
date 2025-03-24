## CatRPG Multimedia Database API

This project is a FastAPI-based RESTful API for uploading and storing multimedia game assets (sprites, audio files, and player scores) in a MongoDB Atlas database. Developed as part of the Database Essentials unit at MCAST.


## Technologies Used
- **Python 3.11**
- **FastAPI** – High-performance API framework
- **Uvicorn** – ASGI server to run FastAPI
- **Motor** – Asynchronous MongoDB driver
- **Pymongo** – Core MongoDB Python driver (used by Motor)
- **Pydantic v2** – Data validation and type enforcement
- **Python-Multipart** – To handle file uploads via Postman
- **Python-Dotenv** – To manage environment variables (if used)
- **Requests** – For making HTTP requests (optional usage)
- **MongoDB Atlas** – Cloud NoSQL database
- **Postman** – For testing your API
- **VS Code** – Development environment



## How I set up the environment
This section outlines how I set up my development environment for this project.

### 1. Created a Project Folder
I created a folder named `catgame_api` to store all the project files.

### 2. Opened VS Code
I opened the folder in Visual Studio Code, which I used as my code editor throughout the assignment.

### 3. Created a Virtual Environment
I opened the terminal in VS Code and ran:
python -m venv env

### 4. Activated the Virtual Environment
In the terminal, I activated the environment using:
.\env\Scripts\activate   

### 5. Installed all required Python packages using pip:
pip install fastapi uvicorn motor pydantic python-dotenv python-multipart requests

### 5. Created requirements.txt
I saved my dependencies by running:
pip freeze > requirements.txt

### 6. Created My Main File
main.py – where all the FastAPI endpoints are



## Running the API Locally

Once your virtual environment and dependencies are ready, run the FastAPI server using:
uvicorn main:app --reload
This will start the API at:

http://127.0.0.1:8000/docs
You can test and view the endpoints using the built-in Swagger UI at that URL.

API Endpoints
| Method | Endpoint          | Description                            |
|--------|-------------------|----------------------------------------|
| POST   | `/upload_sprites` | Upload one or more sprite images       |
| POST   | `/upload_audios`  | Upload one or more audio files         |
| POST   | `/upload_scores`  | Submit one or more player scores       |

All endpoints return JSON responses with confirmation messages and inserted MongoDB IDs.



## 🧪 Testing with Postman

### Uploading Sprites (Multiple):
- Method: POST
- URL: `http://127.0.0.1:8000/upload_sprites`
- Body: `form-data`
- Key: `files` (multiple times)
- Value: Upload PNG images

### Uploading Audio Files (Multiple):
- Method: POST
- URL: `http://127.0.0.1:8000/upload_audios`
- Body: `form-data`
- Key: `files` (multiple times)
- Value: Upload MP3 files

### Submitting Scores (Multiple):
- Method: POST
- URL: `http://127.0.0.1:8000/upload_scores`
- Body: `raw` → `JSON`
[
  { "player_name": "John", "score": 4500 },
  { "player_name": "Jane", "score": 3900 }
]

### Retrieving Sprites
- Method: GET
- URL: `http://127.0.0.1:8000/sprites`
- Description: Returns all uploaded sprite images as base64 strings

### Retrieving Audio Files
- Method: GET
- URL: `http://127.0.0.1:8000/audios`
- Description: Returns all uploaded audio files as base64 strings

### Retrieving Scores
- Method: GET
- URL: `http://127.0.0.1:8000/scores`
- Description: Returns all submitted player scores


## Security Features

### a) Credential Security
- Created a dedicated database user `catdatabase` with **only read/write access**
- Did not use the admin account
- Connection string can be stored securely in `.env` (via `python-dotenv`)

### b) IP Whitelisting
- Restricted access to only **Vercel server IP addresses** and **my home IP**
- Blocked access from public/untrusted addresses

### c) NoSQL Injection Prevention
- Used **Pydantic** models to strictly validate user input
- Added optional regex and type checks (e.g., `^[a-zA-Z0-9_]+$`)
- Never constructed queries using raw user input
- Example protection:

class PlayerScore(BaseModel):
    player_name: str = Field(..., pattern="^[a-zA-Z0-9_]+$")
    score: int = Field(..., ge=0, le=10000)



## Deployment

I deployed the FastAPI app to [Vercel](https://multimedia-cat-rpg-databas-git-1f6bf5-mireyas-projects-4f331778.vercel.app/docs) using the `vercel.json` setup.  

And tested it in Postman using:
- `GET https://multimedia-cat-rpg-database.vercel.app/sprites`
- `POST https://multimedia-cat-rpg-database.vercel.app/upload_scores`
