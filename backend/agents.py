import os
import feedparser
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from newsapi import NewsApiClient
import requests
from gnews import GNews


load_dotenv()

# --- CONFIGURATION ---
llm_fast = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)
llm_creative = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.8)

# Define the State
class AgentState(TypedDict):
    topic: str
    research_summary: str
    draft: str
    critique: str
    revision_count: int
    is_approved: bool
    viral_score: int
    sentiment: str
    target_audience: str
    reading_time_min: int
    seo_keywords: List[str]
    meta_description: str
    image_prompt: str

def is_reliable_source(url: str, title: str) -> bool:
    """Filters out opinion platforms and known low-quality sources."""
    blocked_domains = [
        "medium.com", "linkedin.com", "substack.com", 
        "wordpress.com", "blogspot.com", "tumblr.com"
    ]
    # Check URL
    if any(domain in url.lower() for domain in blocked_domains):
        return False
    # Check Title for clickbait markers (optional but helpful)
    if "opinion:" in title.lower() or "sponsored" in title.lower():
        return False
    return True

# --- TOOL: MULTI-SOURCE AGGREGATOR (ROBUST VERSION) ---
def fetch_tech_news(topic: str) -> str:
    """
    Aggregates news from 6 premium sources with robust error handling.
    """
    print(f"--- 📡 Aggregator: Hunting for '{topic}' across 6 sources ---")
    aggregated_data = []

    # ---------------------------------------------------------
    # SOURCE 1: GNews (General Coverage)
    # ---------------------------------------------------------
    if os.getenv("GNEWS_API_KEY"):
        print(f"   🔍 Checking GNews for '{topic}'...")
        try:
            url = f"https://gnews.io/api/v4/search?q={topic}&lang=en&max=3&apikey={os.getenv('GNEWS_API_KEY')}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                print(f"      ✅ GNews found {len(articles)} articles")
                for article in articles:
                    if is_reliable_source(article['url'], article['title']):
                        aggregated_data.append(f"[GNews] {article['title']} ({article['source']['name']}): {article['description']}")
            else:
                print(f"   ⚠️ GNews Error: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ GNews failed: {e}")

    # ---------------------------------------------------------
    # SOURCE 2: MarketAux (Finance & Market Sentiment)
    # ---------------------------------------------------------
    if os.getenv("MARKETAUX_API_KEY"):
        print(f"   🔍 Checking MarketAux for '{topic}'...")
        try:
            url = f"https://api.marketaux.com/v1/news/all?search={topic}&language=en&limit=2&api_token={os.getenv('MARKETAUX_API_KEY')}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('data', [])
                print(f"      ✅ MarketAux found {len(articles)} articles")
                for article in articles:
                    if is_reliable_source(article['url'], article['title']):
                        # --- SAFE ENTITY EXTRACTION ---
                        entities = article.get('entities', [])
                        sentiment = entities[0].get('sentiment_score', 'N/A') if entities else "N/A"
                        
                        aggregated_data.append(f"[MarketAux - Sentiment: {sentiment}] {article['title']}: {article['description']}")
            else:
                print(f"   ⚠️ MarketAux Error: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ MarketAux failed: {e}")

    # ---------------------------------------------------------
    # SOURCE 3: The New York Times (Safe Mode)
    # ---------------------------------------------------------
    if os.getenv("NYT_API_KEY"):
        print(f"   🔍 Checking NYT for '{topic}'...")
        try:
            params = {
                "q": topic,
                "sort": "newest",
                "fq": 'section_name:("Technology" "Business")',
                "api-key": os.getenv('NYT_API_KEY')
            }
            response = requests.get("https://api.nytimes.com/svc/search/v2/articlesearch.json", params=params)
            
            if response.status_code == 200:
                data = response.json()
                # --- SAFE PARSING ---
                response_body = data.get('response', {})
                if response_body is None: response_body = {}
                
                docs = response_body.get('docs')
                if docs is None: docs = [] # Prevent NoneType error
                
                print(f"      ✅ NYT found {len(docs)} articles")
                # Limit to 2 docs
                for doc in docs[:2]:
                    headline_obj = doc.get('headline', {})
                    if headline_obj and 'main' in headline_obj:
                        pub_date = doc.get('pub_date', '')[:10]
                        aggregated_data.append(f"[NYT - {pub_date}] {headline_obj['main']}: {doc.get('abstract', 'No summary')}")
            else:
                print(f"   ⚠️ NYT Error: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ NYT failed: {e}")

    # ---------------------------------------------------------
    # SOURCE 4: NewsData.io (Breaking Headlines)
    # ---------------------------------------------------------
    if os.getenv("NEWSDATA_API_KEY"):
        print(f"   🔍 Checking NewsData.io for '{topic}'...")
        try:
            url = f"https://newsdata.io/api/1/news?apikey={os.getenv('NEWSDATA_API_KEY')}&q={topic}&language=en"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"      ✅ NewsData found {len(results)} articles")
                for article in results[:2]:
                    if is_reliable_source(article.get('link', ''), article.get('title', '')):
                        aggregated_data.append(f"[NewsData] {article['title']}: {article['description']}")
        except Exception as e:
            print(f"   ⚠️ NewsData failed: {e}")

    # ---------------------------------------------------------
    # SOURCE 5: The Guardian (Deep Analysis)
    # ---------------------------------------------------------
    if os.getenv("GUARDIAN_API_KEY"):
        print(f"   🔍 Checking The Guardian for '{topic}'...")
        try:
            url = f"https://content.guardianapis.com/search?q={topic}&api-key={os.getenv('GUARDIAN_API_KEY')}&show-fields=trailText"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                results = data.get('response', {}).get('results', [])
                print(f"      ✅ Guardian found {len(results)} articles")
                for r in results[:2]:
                    summary = r.get('fields', {}).get('trailText', '')
                    aggregated_data.append(f"[The Guardian] {r['webTitle']}: {summary}")
        except Exception as e:
            print(f"   ⚠️ Guardian failed: {e}")

    # ---------------------------------------------------------
    # SOURCE 6: Google News (Stricter Fallback)
    # ---------------------------------------------------------
    try:
        print(f"   🔍 Checking Google News for '{topic}' (Last 12h)...")
        # Forces new content only (12h period)
        google_news = GNews(max_results=3, period='12h') 
        g_results = google_news.get_news(topic)
        for r in g_results:
            if is_reliable_source(r['url'], r['title']):
                aggregated_data.append(f"[Google News] {r['title']} ({r['publisher']['title']}): {r['url']}")
    except Exception as e:
        print(f"   ⚠️ Google News failed: {e}")

    # ---------------------------------------------------------
    # SOURCE 7: DuckDuckGo (Last Resort)
    # ---------------------------------------------------------
    if len(aggregated_data) < 2:
        try:
            print("   🦆 Checking DuckDuckGo (Last Resort)...")
            with DDGS() as ddgs:
                safe_query = f"{topic} news -site:medium.com -site:linkedin.com -site:substack.com"
                results = list(ddgs.text(keywords=safe_query, region="wt-wt", safesearch="off", timelimit="w", max_results=3))
                for r in results:
                    aggregated_data.append(f"[Web Search] {r['title']}: {r['body']}")
        except Exception as e:
            print(f"   ⚠️ DDGS failed: {e}")

    # ---------------------------------------------------------
    # FINAL ASSEMBLY
    # ---------------------------------------------------------
    result_text = "\n\n".join(aggregated_data)
    
    if not result_text:
        return "CRITICAL: No verified news found. Agents must rely on internal knowledge but declare uncertainty."
    
    return result_text


# --- NODE 1: RESEARCHER (Optimized for APIs) ---
class SearchQueries(BaseModel):
    # We explicitly ask for "Keywords" now, not a "Query"
    search_keywords: str = Field(description="A boolean-style keyword string optimized for news APIs (e.g., 'Nvidia AND AMD AND MI300X')")
    angles: List[str] = Field(description="3 distinct angles to analyze the found news")

def researcher_node(state):
    topic = state["topic"]
    print(f"--- Researcher: Generating Targeted Search for '{topic}' ---")

    # STEP 1: Generate a Keyword-Based Query
    query_generator = llm_fast.with_structured_output(SearchQueries)
    q_result = query_generator.invoke([
        HumanMessage(content=f"""
        We are covering '{topic}'. 
        Generate ONE highly effective KEYWORD search string to find breaking news.
        
        CRITICAL RULES:
        1. Output strictly keywords (e.g. "Stripe IPO valuation", NOT "What is Stripe's IPO valuation?").
        2. Use logical operators if needed (e.g. "Nvidia AND (AMD OR Intel)").
        3. Target a specific, recent event.
        """)
    ])
    
    # We use the keywords for the search
    specific_query = q_result.search_keywords
    angles = q_result.angles
    
    print(f"   🎯 Pivoting Topic: '{topic}' -> Searching for keywords: '{specific_query}'")

    # STEP 2: Search
    raw_data = fetch_tech_news(specific_query)
    
    # Fallback
    if "CRITICAL" in raw_data or len(raw_data) < 50:
        print("   ⚠️ Specific search failed, reverting to broad topic...")
        raw_data = fetch_tech_news(topic)

    # STEP 3: Synthesize
    summary_prompt = f"""
    You are a Lead Tech Analyst. Synthesize this data.
    
    TOPIC: {topic} (Focusing on: {specific_query})
    ANGLES: {angles}
    
    RAW DATA:
    {raw_data}
    """
    summary = llm_creative.invoke([HumanMessage(content=summary_prompt)]).content
    
    return {"research_summary": summary, "search_queries": angles, "topic": specific_query}

# --- NODE 2: WRITER (Journalist Persona) ---
def writer_node(state: AgentState):
    print("--- Writer: Drafting with Style ---")
    topic = state["topic"]
    summary = state["research_summary"]
    angles = state.get("search_queries", ["General Analysis"]) # Use the specific angles found
    
    # We define a "Persona" that adapts based on the topic.
    # For Fintech -> Analytical; For Gadgets -> Witty.
    tone_instruction = "authoritative, data-driven, and slightly skeptical"
    if "crypto" in topic.lower() or "market" in topic.lower():
        tone_instruction = "sharp, financial, and risk-aware (like a Bloomberg columnist)"
    elif "ai" in topic.lower():
        tone_instruction = "futuristic but grounded in reality (like an MIT Tech Review writer)"

    prompt = f"""
    You are a Senior Tech Columnist. Your goal is to write a viral, high-signal article about: {topic}.
    
    ### CONTEXT & ANGLES
    Integrate these specific angles into your narrative: {angles}
    Use this research data as your source of truth: 
    {summary}

    ### STYLE GUIDE ({tone_instruction})
    1. **The Hook:** Start with a specific fact, a quote, or a contrarian statement. NEVER start with "In today's world" or "Technology is advancing."
    2. **Structure:** - Headline
       - The Lead
       - **The Case Study:** Describe a specific technical scenario (e.g. debugging) to illustrate the point. <--- ADDS LENGTH
       - The Meat (Hard Numbers)
       - The Pivot (Risks)
       - The Outlook
    
    CRITICAL: The final output must be **minimum 1,000 words**. Expand on the technical details.
    3. **Formatting:** Use Markdown. Use blockquotes for key stats.

    ### NEGATIVE CONSTRAINTS (CRITICAL)
    - BANNED WORDS: "Delve", "Tapestry", "Game-changer", "Revolutionary", "In conclusion", "Buzzword", "Beacon".
    - No passive voice (e.g., "It was decided"). Use active verbs.
    - Do not sound like a PR press release. Be objective.

    Write the full article now.
    """
    
    # Use the Creative Model (Gemini 1.5 Pro)
    response = llm_creative.invoke([HumanMessage(content=prompt)])
    
    return {"draft": response.content, "revision_count": 0}

# --- NODE 3: EDITOR (The Ruthless Gatekeeper) ---
class EditorOutput(BaseModel):
    is_approved: bool = Field(description="True only if score > 80")
    score: int = Field(description="Quality score 0-100")
    critique: str = Field(description="Bullet points of EXACTLY what needs fixing")
    feedback_type: str = Field(description="One of: 'minor_polish', 'major_rewrite', 'perfect'")

def editor_node(state: AgentState):
    print("--- Editor: Grilling the Draft ---")
    draft = state["draft"]
    topic = state["topic"]
    
    # 1. HARD RULE CHECK (Pre-LLM)
    # We enforce this with code to save tokens and ensure strictness.
    # If these words appear, we auto-penalize.
    banned_words = ["delve", "tapestry", "ever-evolving", "landscape", "game-changer", "moreover", "in conclusion"]
    found_banned = [word for word in banned_words if word in draft.lower()]
    
    banned_warning = ""
    if found_banned:
        banned_warning = f"FATAL ERROR: Found banned AI-cliché words: {found_banned}. These MUST be removed."

    # 2. THE LLM CRITIQUE
    prompt = f"""
    You are the Editor-in-Chief of a top-tier tech publication (like The Verge or Bloomberg).
    Your job is to REJECT mediocrity. You do not fix typos; you fix logic and flow.

    Review this draft about: {topic}

    ### RUBRIC FOR GRADING (0-100):
    1. **The Hook (20pts):** Does the first sentence grab me? Or is it a generic intro?
    2. **Data Density (30pts):** Are there specific numbers, dates, or prices? (e.g. "$5B valuation" vs "a lot of money").
    3. **Tone (30pts):** Is it human/punchy? Or does it sound like a robot?
    4. **Formatting (20pts):** Are there clear headers and short paragraphs?

    ### SPECIFIC INSTRUCTIONS:
    - If you see phrases like "In today's digital world" -> REJECT immediately.
    - If there are no concrete numbers/stats -> REJECT.
    - {banned_warning}

    Draft to Review:
    {draft}
    """
    
    # Use Flash (Fast logic)
    structured_llm = llm_fast.with_structured_output(EditorOutput)
    result = structured_llm.invoke([HumanMessage(content=prompt)])
    
    # Override approval if banned words exist (Hard Logic)
    if found_banned and result.score > 80:
        result.score = 75
        result.is_approved = False
        result.critique = f"Remove these banned words: {found_banned}. " + result.critique

    print(f"   [Editor Verdict] Score: {result.score} | Approved: {result.is_approved}")
    print(f"   [Feedback] {result.critique[:100]}...") # Print first 100 chars of feedback

    return {
        "is_approved": result.is_approved, 
        "critique": result.critique,
        # We pass the score to the state so we can track improvement
        # Note: You might need to add 'score' to your AgentState definition if not already there
    }

# --- NODE 4: REFINER (Surgical Editor) ---
def refiner_node(state: AgentState):
    print(f"--- Refiner: Polishing (Revision {state['revision_count'] + 1}) ---")
    draft = state["draft"]
    critique = state["critique"]
    
    # We use Pro because rewriting requires high nuance to not lose the 'voice'
    # We explicitly tell it to PRESERVE the good parts.
    prompt = f"""
    You are a Senior Editor. Your job is to fix specific issues in the draft without ruining the voice.
    
    CRITIQUE TO ADDRESS: 
    {critique}
    
    INSTRUCTIONS:
    1. Read the critique carefully.
    2. Only rewrite the sections that triggered the critique. 
    3. Do NOT rewrite the whole article if the rest is good.
    4. Maintain the "Journalist" tone (authoritative, no fluff).
    5. If the critique asks for data, insert placeholders like [Data: market cap needed] if you can't find it, but try to smooth it over.

    Current Draft:
    {draft}
    
    Return the FULL, polished final version of the blog post.
    """
    
    response = llm_creative.invoke([HumanMessage(content=prompt)])
    
    return {
        "draft": response.content, 
        "revision_count": state["revision_count"] + 1,
        # We clear the critique so the next loop (if any) starts fresh
        "critique": "" 
    }

# --- NODE 5: SEO & PACKAGING (The Growth Marketer) ---

class DistributionPackage(BaseModel):
    # Titles
    title_seo: str = Field(description="Optimized for Google Search (Keyphrase first)")
    title_viral: str = Field(description="Clickbaity/High-CTR title for social media")
    slug: str = Field(description="URL-friendly slug (e.g., ai-agent-tutorial)")
    
    # Meta
    meta_description: str = Field(description="155 chars max, high urgency")
    tags: List[str] = Field(description="5 relevant tags")
    reading_time: int = Field(description="Estimated minutes")
    
    # Social Media Assets
    linkedin_post: str = Field(description="Professional, emoji-moderate, engagement-focused post")
    twitter_thread_hook: str = Field(description="First tweet of a thread (hook)")
    
    # Visuals
    image_prompt_midjourney: str = Field(description="Detailed artistic prompt for Midjourney/DALL-E")
    image_alt_text: str = Field(description="Accessibility text for the image")

def seo_node(state: AgentState):
    print("--- SEO: Packaging for Distribution ---")
    draft = state["draft"]
    topic = state["topic"]
    
    prompt = f"""
    You are a VP of Marketing. The blog post is written. Now package it for maximum views.
    
    Analyze this draft:
    {draft[:4000]}... (truncated)
    
    TASKS:
    1. **Titles:** Generate an SEO title (boring, accurate) and a Viral title (creates curiosity gap).
    2. **Socials:** Write a LinkedIn post that sounds like a thought leader (not a bot). Write a Twitter hook that makes people stop scrolling.
    3. **Visuals:** Describe a header image that is abstract and modern (Cyberpunk/Minimalist/Tech). NO TEXT in the image description.
    """
    
    # Use Flash for this. It's great at following strict schemas.
    structured_llm = llm_fast.with_structured_output(DistributionPackage)
    result = structured_llm.invoke([HumanMessage(content=prompt)])
    
    print(f"   [SEO] Viral Title: {result.title_viral}")
    
    # We save this as a dictionary to store in Supabase JSON column later
    return {
        "final_metadata": result.dict()
    }

# --- NODE 6: PUBLISHER (Dev.to) ---
def publish_to_devto(state: AgentState):
    """
    Publishes the approved draft to Dev.to using their API.
    """
    print("--- Publisher: Uploading to Dev.to ---")
    
    if not os.getenv("DEVTO_API_KEY"):
        print("   ⚠️ DEVTO_API_KEY not found. Skipping publication.")
        return {"publish_status": "skipped"}

    # 1. Prepare Payload
    # Dev.to requires a specific format. We add the 'ai-generated' tag for safety.
    # We use the 'title_viral' from SEO node, or fallback to topic
    title = state.get("final_metadata", {}).get("title_viral", f"Deep Dive: {state['topic']}")
    tags = state.get("final_metadata", {}).get("tags", [])
    
    # Ensure tags are lowercase and alphanumeric (Dev.to requirement)
    clean_tags = [t.lower().replace(" ", "") for t in tags]
    clean_tags = clean_tags[:4] # Dev.to allows max 4 tags
    if "ai" not in clean_tags: clean_tags.append("ai")
    
    article_payload = {
        "article": {
            "title": title,
            "body_markdown": state["draft"],
            "published": False, # Set to True to auto-publish, False for Draft
            "tags": clean_tags,
            "series": "TrendFlow AI Digest"
        }
    }
    
    # 2. Send Request
    headers = {
        "api-key": os.getenv("DEVTO_API_KEY"),
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post("https://dev.to/api/articles", json=article_payload, headers=headers)
        
        if response.status_code == 201:
            print(f"   ✅ Published to Dev.to! URL: {response.json()['url']}")
            return {"publish_status": "success", "publish_url": response.json()['url']}
        else:
            print(f"   ❌ Failed to publish: {response.text}")
            return {"publish_status": "failed"}
    except Exception as e:
        print(f"   ❌ Publisher Exception: {e}")
        return {"publish_status": "error"}

# --- UPDATED STATE DEFINITION ---
# This matches the data output by your new advanced nodes
class AgentState(TypedDict):
    topic: str
    search_queries: List[str]   # Added for Researcher
    research_summary: str
    draft: str
    critique: str
    revision_count: int
    is_approved: bool
    score: int                  # Added for Editor
    final_metadata: dict        # Added for SEO
    publish_status: str         # Added for Publisher
    publish_url: str            # Added for Publisher

# --- LOGIC FLOW ---
def check_approval(state: AgentState):
    """
    Determines the next step based on the Editor's verdict.
    """
    # 1. If approved by Editor, go to SEO
    if state["is_approved"]:
        return "approved"
    
    # 2. Safety Valve: If we have revised 2 times already, stop the loop.
    # We force it to 'approved' (SEO) to avoid an infinite loop or crashing.
    if state["revision_count"] >= 2:
        print("--- ⚠️ Max revisions reached. Proceeding to SEO regardless. ---")
        return "approved"
    
    # 3. Otherwise, go back to Refiner
    return "rejected"

# --- GRAPH BUILD ---
workflow = StateGraph(AgentState)

# 1. Add All Nodes
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("editor", editor_node)
workflow.add_node("refiner", refiner_node)
workflow.add_node("seo", seo_node)
workflow.add_node("publisher", publish_to_devto)

# 2. Set Entry Point
workflow.set_entry_point("researcher")

# 3. Standard Edges (Linear Flow)
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "editor")

# 4. Conditional Edges (The Quality Loop)
workflow.add_conditional_edges(
    "editor",          # The node where the decision happens
    check_approval,    # The function that decides 'approved' vs 'rejected'
    {
        "approved": "seo",      # If approved -> Go to SEO
        "rejected": "refiner"   # If rejected -> Go to Refiner
    }
)

# 5. Loop Back
workflow.add_edge("refiner", "editor") # After refining, send back to Editor for re-check

# 6. End
workflow.add_edge("seo", "publisher")
workflow.add_edge("publisher", END)

# 7. Compile
app_graph = workflow.compile()