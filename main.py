from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
from supabase import create_client, Client
from datetime import datetime

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

#visit model

class Visit(BaseModel):
    user_email: str
    customer_name: str
    visit_date: str  # Format: YYYY-MM-DD
    purpose: str
    notes: str

@app.post("/visits")
def add_visit(visit: Visit):
    data = {
        "user_email": visit.user_email,
        "customer_name": visit.customer_name,
        "visit_date": visit.visit_date,
        "purpose": visit.purpose,
        "notes": visit.notes
    }
    response = supabase.table("visits").insert(data).execute()
    return {"status": "success", "data": response.data}

class CreateUserRequest(BaseModel):
    email: str
    password: str
    name: str       # 👈 Add this
    role: str
    admin_token: str

@app.post("/create-user")
def create_user(req: CreateUserRequest):
    if req.admin_token != "letmeinadmin":
        return {"error": "Unauthorized"}

    # Step 1: Create auth user
    auth_url = f"{url}/auth/v1/admin/users"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": req.email,
        "password": req.password,
        "name": req.name,
        "email_confirm": True
    }

    auth_res = requests.post(auth_url, json=payload, headers=headers)
    if auth_res.status_code != 200:
        return {"error": "Failed to create auth user", "details": auth_res.json()}

    user_id = auth_res.json().get("user", {}).get("id")

    # Step 2: Insert into your users table with UID
    insert_url = f"{url}/rest/v1/users"
    insert_headers = headers.copy()
    insert_headers["Prefer"] = "return=minimal"

    data = {
        "id": user_id,  # assuming your users table has a 'id' column as FK
        "email": req.email,
        "role": req.role
    }

    insert_res = requests.post(insert_url, json=data, headers=insert_headers)
    if insert_res.status_code != 201:
        return {"error": "Failed to insert into users table", "details": insert_res.text}

    return {"success": True}

