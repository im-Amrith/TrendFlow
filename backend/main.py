import os
import requests
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(".env.local") # Always try to load .env.local to pick up new keys like HASHNODE_TOKEN

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

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or "PLACEHOLDER" in SUPABASE_URL:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not set or is a placeholder.")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
        supabase = None

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt
from datetime import datetime, timedelta

# ... existing code ...

# Auth Models
class GoogleAuthRequest(BaseModel):
    credential: str

class User(BaseModel):
    id: str
    email: str
    name: str
    picture: str

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user_id
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@app.post("/auth/google")
async def google_auth(request: GoogleAuthRequest):
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            request.credential, 
            google_requests.Request(), 
            clock_skew_in_seconds=10
        )

        # Extract user info
        email = idinfo['email']
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        google_id = idinfo['sub']

        # Check/Create user in Supabase
        user_id = google_id # Default to Google ID if DB fails
        
        if supabase:
            try:
                # Check if user exists
                existing = supabase.table("users").select("*").eq("email", email).execute()
                
                if existing.data:
                    user_id = existing.data[0]['id']
                    # Update info if needed
                    supabase.table("users").update({
                        "full_name": name,
                        "avatar_url": picture
                    }).eq("id", user_id).execute()
                else:
                    # Create new user
                    new_user = supabase.table("users").insert({
                        "email": email,
                        "full_name": name,
                        "avatar_url": picture
                    }).execute()
                    user_id = new_user.data[0]['id']
            except Exception as e:
                print(f"Database auth error: {e}")
                # Continue without DB persistence if it fails (fallback mode)

        # Create JWT
        access_token = create_access_token(data={"sub": user_id, "email": email, "name": name, "picture": picture})
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

# User Settings Models & Endpoints
class UserSettings(BaseModel):
    devto_api_key: Optional[str] = None
    hashnode_token: Optional[str] = None
    hashnode_pub_id: Optional[str] = None

@app.get("/user/settings")
async def get_user_settings(user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        response = supabase.table("users").select("devto_api_key, hashnode_token, hashnode_pub_id").eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = response.data[0]
        
        return {
            "devto_configured": bool(user.get("devto_api_key")),
            "hashnode_configured": bool(user.get("hashnode_token") and user.get("hashnode_pub_id")),
            "devto_api_key": user.get("devto_api_key"),
            "hashnode_token": user.get("hashnode_token"),
            "hashnode_pub_id": user.get("hashnode_pub_id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/user/settings")
async def update_user_settings(settings: UserSettings, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        update_data = {k: v for k, v in settings.dict().items() if v is not None}
        # Allow clearing keys if empty string is passed (frontend might send empty string)
        # But pydantic Optional[str] might be None if not sent. 
        # If user sends "", we should probably save it as null or empty string.
        # Let's assume frontend sends what it wants to save.
        
        if not update_data:
            return {"message": "No changes"}
            
        supabase.table("users").update(update_data).eq("id", user_id).execute()
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
        "hashnode": [],
        "totals": {"views": 0, "reactions": 0, "comments": 0}
    }

    if not supabase:
        return analytics_data

    # Fetch user keys
    try:
        user_res = supabase.table("users").select("devto_api_key, hashnode_token, hashnode_pub_id").eq("id", user_id).execute()
        if not user_res.data:
            return analytics_data
        user_keys = user_res.data[0]
    except Exception as e:
        print(f"Error fetching user keys: {e}")
        return analytics_data
    
    devto_key = user_keys.get("devto_api_key") or os.getenv("DEVTO_API_KEY")
    hashnode_token = user_keys.get("hashnode_token") or os.getenv("HASHNODE_TOKEN")
    hashnode_pub_id = user_keys.get("hashnode_pub_id") or os.getenv("HASHNODE_PUB_ID")

    async def fetch_devto(client):
        if not devto_key: return []
        try:
            resp = await client.get("https://dev.to/api/articles/me/published", headers={"api-key": devto_key})
            return resp.json() if resp.status_code == 200 else []
        except Exception as e:
            print(f"Dev.to Analytics Error: {e}")
            return []

    async def fetch_hashnode(client):
        if not (hashnode_token and hashnode_pub_id): return []
        try:
            query = """
            query GetPosts($publicationId: ObjectId!) {
              publication(id: $publicationId) {
                posts(first: 20) {
                  edges {
                    node {
                      title
                      url
                      publishedAt
                      views
                      reactionCount
                      responseCount
                    }
                  }
                }
              }
            }
            """
            resp = await client.post(
                "https://gql.hashnode.com", 
                json={"query": query, "variables": {"publicationId": hashnode_pub_id}}, 
                headers={"Authorization": hashnode_token, "Content-Type": "application/json"}
            )
            data = resp.json()
            if resp.status_code == 200 and "data" in data and data["data"]["publication"]:
                return data["data"]["publication"]["posts"]["edges"]
        except Exception as e:
            print(f"Hashnode Analytics Error: {e}")
        return []

    async with httpx.AsyncClient() as client:
        devto_res, hashnode_res = await asyncio.gather(fetch_devto(client), fetch_hashnode(client))

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

    # Process Hashnode
    for edge in hashnode_res:
        node = edge["node"]
        views = node.get("views", 0)
        reactions = node.get("reactionCount", 0)
        comments = node.get("responseCount", 0)
        
        analytics_data["hashnode"].append({
            "title": node["title"],
            "url": node["url"],
            "views": views,
            "reactions": reactions,
            "comments": comments,
            "published_at": node["publishedAt"]
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

@app.get("/posts")
async def get_posts(user_id: str = Depends(get_current_user)):
    if not supabase:
        return []
    try:
        # Filter posts by user_id
        response = supabase.table("posts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

@app.put("/posts/{post_id}")
async def update_post(post_id: str, post: PostUpdate, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        # Filter out None values
        update_data = {k: v for k, v in post.dict().items() if v is not None}
        # Ensure user owns the post
        response = supabase.table("posts").update(update_data).eq("id", post_id).eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        response = supabase.table("posts").delete().eq("id", post_id).eq("user_id", user_id).execute()
        return {"message": "Post deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts/{post_id}/publish")
async def publish_post_to_devto(post_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    # Fetch user keys
    user_res = supabase.table("users").select("devto_api_key").eq("id", user_id).execute()
    devto_key = None
    if user_res.data:
        devto_key = user_res.data[0].get("devto_api_key")
    
    # Fallback to env
    if not devto_key:
        devto_key = os.getenv("DEVTO_API_KEY")

    if not devto_key:
        raise HTTPException(status_code=400, detail="Dev.to API Key not configured in Settings")

    try:
        # 1. Fetch the post
        response = supabase.table("posts").select("*").eq("id", post_id).eq("user_id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post = response.data[0]
        
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
                "title": post.get("title"),
                "body_markdown": post.get("content_markdown") or "No content generated.",
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
            supabase.table("posts").update({"status": "published"}).eq("id", post_id).eq("user_id", user_id).execute()
            return {"status": "success", "url": devto_res.json()['url']}
        else:
            print(f"❌ Dev.to Error ({devto_res.status_code}): {devto_res.text}")
            raise HTTPException(status_code=500, detail=f"Dev.to Error: {devto_res.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts/{post_id}/publish/hashnode")
async def publish_post_to_hashnode(post_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    # Fetch user keys
    user_res = supabase.table("users").select("hashnode_token, hashnode_pub_id").eq("id", user_id).execute()
    token = None
    pub_id = None
    
    if user_res.data:
        token = user_res.data[0].get("hashnode_token")
        pub_id = user_res.data[0].get("hashnode_pub_id")
        
    # Fallback
    if not token: token = os.getenv("HASHNODE_TOKEN")
    if not pub_id: pub_id = os.getenv("HASHNODE_PUB_ID")
    
    if not token or not pub_id:
        print(f"❌ Hashnode Config Missing. Token: {'Set' if token else 'Missing'}, Pub ID: {'Set' if pub_id else 'Missing'}")
        raise HTTPException(status_code=400, detail="Hashnode Token or Publication ID not configured in Settings")

    try:
        # 1. Fetch the post
        response = supabase.table("posts").select("*").eq("id", post_id).eq("user_id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post = response.data[0]
        
        # 2. Prepare Payload for Hashnode
        tags = post.get("seo_keywords", [])
        if not isinstance(tags, list):
            tags = []
            
        # Hashnode tags format: [{"slug": "tag", "name": "Tag"}]
        formatted_tags = []
        for t in tags:
            clean = t.replace("#", "").strip()
            if clean:
                formatted_tags.append({"slug": clean.lower().replace(" ", "-"), "name": clean})
        
        formatted_tags = formatted_tags[:5] # Limit to 5

        url = "https://gql.hashnode.com"
        headers = {
            "Authorization": os.getenv("HASHNODE_TOKEN"),
            "Content-Type": "application/json"
        }
        
        # GraphQL Mutation
        query = """
        mutation PublishPost($input: PublishPostInput!) {
          publishPost(input: $input) {
            post {
              url
              slug
            }
          }
        }
        """
        
        variables = {
            "input": {
                "title": post.get("title"),
                "contentMarkdown": post.get("content_markdown") or "No content generated.",
                "publicationId": os.getenv("HASHNODE_PUB_ID"),
                "tags": formatted_tags
            }
        }
        
        print(f"Sending payload to Hashnode: {variables}")
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Hashnode GraphQL Error: {data['errors']}")
                raise HTTPException(status_code=500, detail=f"Hashnode Error: {data['errors'][0]['message']}")
            
            post_url = data["data"]["publishPost"]["post"]["url"]
            
            # 4. Update local status
            supabase.table("posts").update({"status": "published"}).eq("id", post_id).eq("user_id", user_id).execute()
            return {"status": "success", "url": post_url}
        else:
            print(f"❌ Hashnode HTTP Error ({response.status_code}): {response.text}")
            raise HTTPException(status_code=500, detail=f"Hashnode HTTP Error: {response.text}")

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
        
        # Prepare data for Supabase
        post_data = {
            "user_id": user_id,
            "title": metadata.get("title_viral", f"Deep Dive: {request.topic}"),
            "content_markdown": final_state.get("draft", ""),
            "status": "needs_review",
            "viral_score": 85, # Default value as new SEO node doesn't generate score
            "sentiment": "Neutral", # Default value
            "target_audience": "General Tech", # Default value
            "reading_time_min": metadata.get("reading_time", 5),
            "seo_keywords": metadata.get("tags", []),
            "meta_description": metadata.get("meta_description", ""),
            "critique_notes": final_state.get("critique", "No critique generated"),
            "image_prompt": metadata.get("image_prompt_midjourney", "")
        }
        
        # Insert into Supabase
        if supabase:
            try:
                response = supabase.table("posts").insert(post_data).execute()
                return {"status": "success", "data": response.data[0], "state": final_state}
            except Exception as e:
                print(f"Supabase Insert Failed: {e}")
                # Fallback: Return the data anyway so the UI can display it
                # We add a fake ID so the frontend doesn't crash
                post_data["id"] = "temp-" + os.urandom(4).hex()
                post_data["created_at"] = "2024-01-01T00:00:00Z"
                return {"status": "partial_success", "data": post_data, "message": "Content generated but failed to save to DB (Table missing?)."}
        else:
            post_data["id"] = "temp-" + os.urandom(4).hex()
            post_data["created_at"] = "2024-01-01T00:00:00Z"
            return {"status": "success", "data": post_data, "message": "Supabase not configured, returning data directly."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
