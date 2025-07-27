from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_ROLE")
supabase: Client = create_client(url, key)

@app.get("/")
def root():
    return {"message": "Backend running"}

@app.get("/semiconductor-info")
def get_info():
    return {"text": "Semiconductors are the foundation of modern electronics and computing."}

# Feedback model
class Feedback(BaseModel):
    user_email: str
    message: str

@app.post("/feedback")
def post_feedback(feedback: Feedback):
    data = {
        "user_email": feedback.user_email,
        "message": feedback.message
    }
    response = supabase.table("feedbacks").insert(data).execute()
    return {"status": "success", "data": response.data}
