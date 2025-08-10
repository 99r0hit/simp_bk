from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from supabase import create_client, Client
from typing import Optional

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# -------------------------
# AUTH AND DEPENDENCIES
# -------------------------

class LoginRequest(BaseModel):
    email: str
    password: str

def get_current_user(request: Request):
    email = request.headers.get("x-user-email")
    if not email:
        raise HTTPException(status_code=401, detail="User email header missing")
    
    response = supabase.table("users").select("*").eq("email", email).single().execute()
    user = response.data
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@app.post("/login")
def login(req: LoginRequest):
    response = supabase.table("users").select("*").eq("email", req.email).eq("password", req.password).execute()
    if response.data and len(response.data) > 0:
        user = response.data[0]
        return {"success": True, "user": user}
    else:
        return {"success": False, "message": "Invalid credentials"}

# -------------------------
# OPPORTUNITIES
# -------------------------

class Opportunity(BaseModel):
    customer: str
    description: str
    notes: str
    stage: int

@app.post("/opportunity")
def create_opportunity(op: Opportunity, user=Depends(get_current_user)):
    supabase.table("opportunities").insert({
        "user_id": user["id"],
        "customer": op.customer,
        "description": op.description,
        "notes": op.notes,
        "stage": op.stage
    }).execute()
    return {"message": "Opportunity created"}

@app.put("/opportunity/{id}")
def update_opportunity(id: str, op: Opportunity, user=Depends(get_current_user)):
    supabase.table("opportunities").update({
        "customer": op.customer,
        "description": op.description,
        "notes": op.notes,
        "stage": op.stage
    }).eq("id", id).eq("user_id", user["id"]).execute()
    return {"message": "Opportunity updated"}

@app.get("/opportunities")
def get_opportunities(user=Depends(get_current_user)):
    result = (
        supabase
        .table("opportunities")
        .select("id, project, stage, description, notes, customer(name)")
        .eq("user_id", user["id"])
        .execute()
    )
    return result.data


# -------------------------
# VISITS
# -------------------------

class Visits(BaseModel):
    date: str
    customer: str
    purpose: str
    notes: str
    location: str

@app.post("/visits")
def create_visit(visits: Visits, user=Depends(get_current_user)):
    supabase.table("visits").insert({
        "user_id": user["id"],
        "date": visits.date,
        "customer": visits.customer,
        "purpose": visits.purpose,
        "notes": visits.notes
    }).execute()
    return {"message": "Visit logged"}

@app.put("/visits/{id}")
def update_visit(id: str, visits: Visits, user=Depends(get_current_user)):
    supabase.table("visits").update({
        "date": visits.date,
        "customer": visits.customer,
        "purpose": visits.purpose,
        "description": visits.description
    }).eq("id", id).eq("user_id", user["id"]).execute()
    return {"message": "Visit updated"}

@app.get("/visits")
def get_visits(user=Depends(get_current_user)):
    result = supabase.table("visits").select("*").eq("user_id", user["id"]).execute()
    return result.data

# -------------------------
# FEEDBACK (optional)
# -------------------------

class Feedback(BaseModel):
    user_email: str
    message: str

@app.post("/feedback")
def post_feedback(feedback: Feedback):
    response = supabase.table("feedbacks").insert({
        "user_email": feedback.user_email,
        "message": feedback.message
    }).execute()
    return {"status": "success", "data": response.data}

# class CreateUserRequest(BaseModel):
#     email: str
#     password: str
#     name: str       # 👈 Add this
#     role: str
#     admin_token: str

# @app.post("/create-user")
# def create_user(req: CreateUserRequest):
#     if req.admin_token != "letmeinadmin":
#         return {"error": "Unauthorized"}

#     # Step 1: Create auth user
#     auth_url = f"{url}/auth/v1/admin/users"
#     headers = {
#         "apikey": key,
#         "Authorization": f"Bearer {key}",
#         "Content-Type": "application/json",
#     }
#     payload = {
#         "email": req.email,
#         "password": req.password,
#         "name": req.name,
#         "email_confirm": True
#     }

#     auth_res = requests.post(auth_url, json=payload, headers=headers)
#     if auth_res.status_code != 200:
#         return {"error": "Failed to create auth user", "details": auth_res.json()}

#     user_id = auth_res.json().get("user", {}).get("id")

#     # Step 2: Insert into your users table with UID
#     insert_url = f"{url}/rest/v1/users"
#     insert_headers = headers.copy()
#     insert_headers["Prefer"] = "return=minimal"

#     data = {
#         "id": user_id,  # assuming your users table has a 'id' column as FK
#         "email": req.email,
#         "role": req.role,
#         "name": req.name,
#     }

#     insert_res = requests.post(insert_url, json=data, headers=insert_headers)
#     if insert_res.status_code != 201:
#         return {"error": "Failed to insert into users table", "details": insert_res.text}

#     return {"success": True}





