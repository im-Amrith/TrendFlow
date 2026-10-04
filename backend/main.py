import os
import json
import requests
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, firestore

# Load environment variables
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env.local"))

try:
    from backend.agents import app_graph
    from backend.news_fetcher import fetch_structured_news
except ImportError:
    from agents import app_graph
    from news_fetcher import fetch_structured_news

# Initialize FastAPI
app = FastAPI(title="TrendFlow Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase Admin
# Credentials, in order of preference:
#   1. FIREBASE_SERVICE_ACCOUNT  - full service-account JSON as a string (use this as a Hugging Face Space secret)
#   2. GOOGLE_APPLICATION_CREDENTIALS - path to the key file (relative paths resolve from this folder)
#   3. Application default credentials
def init_firebase():
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if service_account_json:
        return firebase_admin.initialize_app(credentials.Certificate(json.loads(service_account_json)))

    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase-key.json")
    if not os.path.isabs(key_path):
        key_path = os.path.join(BACKEND_DIR, key_path)
    if os.path.exists(key_path):
        return firebase_admin.initialize_app(credentials.Certificate(key_path))
    return firebase_admin.initialize_app()

try:
    if not firebase_admin._apps:
        init_firebase()
    db = firestore.client()
except Exception as e:
    print(f"Warning: Failed to initialize Firebase Admin client: {e}")
    db = None

from datetime import datetime

# ... existing code ...

# Auth Models
class User(BaseModel):
    id: str
    email: str
    name: str
    picture: str

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        
        # Ensure user exists in our users collection
        if db:
            user_ref = db.collection("users").document(uid)
            doc = user_ref.get()
            if not doc.exists:
                user_ref.set({
                    "email": email,
                    "created_at": firestore.SERVER_TIMESTAMP
                }, merge=True)
        return uid
    except Exception as e:
        print("Firebase verification error:", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

# User Settings Models & Endpoints
class UserSettings(BaseModel):
    devto_api_key: Optional[str] = None

@app.get("/user/settings")
async def get_user_settings(user_id: str = Depends(get_current_user)):
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = doc.to_dict()
        
        return {
            "devto_configured": bool(user_data.get("devto_api_key")),
            "devto_api_key": user_data.get("devto_api_key")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/user/settings")
async def update_user_settings(settings: UserSettings, user_id: str = Depends(get_current_user)):
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        update_data = {k: v for k, v in settings.dict().items() if v is not None}
        
        if not update_data:
            return {"message": "No changes"}
            
        user_ref = db.collection("users").document(user_id)
        user_ref.set(update_data, merge=True)
        return {"message": "Settings updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Request Models
class BlogRequest(BaseModel):
    topic: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content_markdown: Optional[str] = None
    status: Optional[str] = None
    viral_score: Optional[int] = None
    sentiment: Optional[str] = None
    target_audience: Optional[str] = None
    reading_time_min: Optional[int] = None
    seo_keywords: Optional[List[str]] = None
    meta_description: Optional[str] = None
    critique_notes: Optional[str] = None
    image_prompt: Optional[str] = None

@app.get("/analytics")
async def get_analytics(user_id: str = Depends(get_current_user)):
    analytics_data = {
        "devto": [],
        "totals": {"views": 0, "reactions": 0, "comments": 0}
    }

    if not db:
        return analytics_data

    # Fetch user keys
    try:
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        if not doc.exists:
            return analytics_data
        user_keys = doc.to_dict()
    except Exception as e:
        print(f"Error fetching user keys: {e}")
        return analytics_data
    
    devto_key = user_keys.get("devto_api_key")

    async def fetch_devto(client):
        if not devto_key: return []
        try:
            resp = await client.get("https://dev.to/api/articles/me/published", headers={"api-key": devto_key})
            return resp.json() if resp.status_code == 200 else []
        except Exception as e:
            print(f"Dev.to Analytics Error: {e}")
            return []

    async with httpx.AsyncClient() as client:
        devto_res = await fetch_devto(client)

    # Process Dev.to
    for art in devto_res:
        views = art.get("page_views_count", 0)
        reactions = art.get("public_reactions_count", 0)
        comments = art.get("comments_count", 0)
        
        analytics_data["devto"].append({
            "title": art["title"],
            "url": art["url"],
            "views": views,
            "reactions": reactions,
            "comments": comments,
            "published_at": art["published_at"]
        })
        analytics_data["totals"]["views"] += views
        analytics_data["totals"]["reactions"] += reactions
        analytics_data["totals"]["comments"] += comments

    return analytics_data

@app.get("/news")
async def get_news(topic: str = "Technology", limit: int = 5):
    try:
        news = await fetch_structured_news(topic, limit)
        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts")
async def get_posts(user_id: str = Depends(get_current_user)):
    if not db:
        return []
    try:
        # Filter posts by user_id, order by created_at desc
        posts_ref = db.collection("drafts").where("user_id", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING)
        docs = posts_ref.stream()
        
        posts = []
        for doc in docs:
            post_data = doc.to_dict()
            post_data["id"] = doc.id
            posts.append(post_data)
            
        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

@app.put("/posts/{post_id}")
async def update_post(post_id: str, post: PostUpdate, user_id: str = Depends(get_current_user)):
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        update_data = {k: v for k, v in post.dict().items() if v is not None}
        
        post_ref = db.collection("drafts").document(post_id)
        doc = post_ref.get()
        if not doc.exists or doc.to_dict().get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Post not found or unauthorized")
            
        post_ref.update(update_data)
        
        # Return updated document
        updated_doc = post_ref.get().to_dict()
        updated_doc["id"] = post_id
        return updated_doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, user_id: str = Depends(get_current_user)):
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        post_ref = db.collection("drafts").document(post_id)
        doc = post_ref.get()
        if not doc.exists or doc.to_dict().get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Post not found or unauthorized")
            
        post_ref.delete()
        return {"message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts/{post_id}/publish")
async def publish_post_to_devto(post_id: str, user_id: str = Depends(get_current_user)):
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    # Fetch user keys
    user_ref = db.collection("users").document(user_id)
    doc = user_ref.get()
    devto_key = None
    if doc.exists:
        devto_key = doc.to_dict().get("devto_api_key")

    if not devto_key:
        raise HTTPException(status_code=400, detail="Dev.to API Key not configured in Settings")

    try:
        # 1. Fetch the post
        post_ref = db.collection("drafts").document(post_id)
        post_doc = post_ref.get()
        if not post_doc.exists or post_doc.to_dict().get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post = post_doc.to_dict()

        # 2. Prepare Payload for Dev.to
        tags = post.get("seo_keywords", [])
        if not isinstance(tags, list):
            tags = []
            
        # Clean tags: remove #, spaces, and non-alphanumeric chars (Dev.to is strict)
        clean_tags = []
        for t in tags:
            # Remove # and spaces
            cleaned = t.lower().replace("#", "").replace(" ", "")
            # Keep only alphanumeric
            cleaned = "".join(c for c in cleaned if c.isalnum())
            if cleaned:
                clean_tags.append(cleaned)
        
        clean_tags = clean_tags[:3] # Limit to 3 to leave room for 'ai'
        if "ai" not in clean_tags: clean_tags.append("ai")

        article_payload = {
            "article": {
                "title": post.get("title_viral") or post.get("topic", "TrendFlow AI Digest"),
                "body_markdown": post.get("draft_content") or "No content generated.",
                "published": True, # Publish immediately
                "tags": clean_tags,
                "series": "TrendFlow AI Digest"
            }
        }

        # 3. Send to Dev.to
        headers = {
            "api-key": devto_key,
            "Content-Type": "application/json"
        }
        
        print(f"Sending payload to Dev.to: {article_payload}")
        devto_res = requests.post("https://dev.to/api/articles", json=article_payload, headers=headers)
        
        if devto_res.status_code == 201:
            # 4. Update local status
            post_ref.update({"status": "published"})
            return {"status": "success", "url": devto_res.json()['url']}
        else:
            print(f"❌ Dev.to Error ({devto_res.status_code}): {devto_res.text}")
            raise HTTPException(status_code=500, detail=f"Dev.to Error: {devto_res.text}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-pro-blog")
async def generate_pro_blog(request: BlogRequest, user_id: str = Depends(get_current_user)):
    try:
        print(f"Starting generation for topic: {request.topic} by user {user_id}")
        
        # Initial State
        initial_state = {
            "topic": request.topic,
            "revision_count": 0,
            "is_approved": False
        }
        
        # Run the Graph
        final_state = app_graph.invoke(initial_state)
        
        # Extract metadata safely
        metadata = final_state.get("final_metadata", {})
        
        # Prepare data for Firestore drafts collection
        post_data = {
            "user_id": user_id,
            "topic": request.topic,
            "title": metadata.get("title_viral", f"Deep Dive: {request.topic}"),
            "title_viral": metadata.get("title_viral", f"Deep Dive: {request.topic}"),
            "draft_content": final_state.get("draft", ""),
            "content_markdown": final_state.get("draft", ""),
            "status": "needs_review",
            "viral_score": 85,
            "sentiment": "Neutral",
            "target_audience": "General Tech",
            "reading_time_min": metadata.get("reading_time", 5),
            "seo_keywords": metadata.get("tags", []),
            "tags": metadata.get("tags", []),
            "meta_description": metadata.get("meta_description", ""),
            "critique_notes": final_state.get("critique", "No critique generated"),
            "image_prompt": metadata.get("image_prompt_midjourney", ""),
            "is_approved": False,
            "revision_count": 0,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        # Insert into Firestore
        if db:
            try:
                # Add auto-generated document ID to drafts
                doc_ref = db.collection("drafts").document()
                doc_ref.set(post_data)

                # Fetch it back so created_at is the real timestamp, not the SERVER_TIMESTAMP sentinel (not JSON serializable)
                post_data = doc_ref.get().to_dict()
                post_data["id"] = doc_ref.id
                return {"status": "success", "data": post_data, "state": final_state}
            except Exception as e:
                print(f"Firestore Insert Failed: {e}")
                # Fallback: Return
                post_data["id"] = "temp-" + os.urandom(4).hex()
                post_data["created_at"] = datetime.now().isoformat()
                return {"status": "partial_success", "data": post_data, "state": final_state, "message": "Content generated but failed to save to DB."}
        else:
            post_data["id"] = "temp-" + os.urandom(4).hex()
            post_data["created_at"] = datetime.now().isoformat()
            return {"status": "success", "data": post_data, "state": final_state, "message": "Database not configured, returning data directly."}
    except Exception as e:
        print(f"Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
