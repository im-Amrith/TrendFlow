import os
import time
from datetime import date
import threading
from collections import deque
import feedparser
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from newsapi import NewsApiClient
import requests
from gnews import GNews


load_dotenv()

# --- CONFIGURATION ---
# Groq free tier. Limits are per model, so splitting work across two models doubles our token budget.
FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "openai/gpt-oss-20b")
CREATIVE_MODEL = os.getenv("GROQ_CREATIVE_MODEL", "openai/gpt-oss-120b")
GROQ_TPM_LIMIT = int(os.getenv("GROQ_TPM_LIMIT", "8000"))  # tokens per minute, per model
GROQ_RPM_LIMIT = int(os.getenv("GROQ_RPM_LIMIT", "30"))    # requests per minute, per model

class RateLimitGuard:
    """Sliding 60s window of tokens/requests for one model. Blocks until a call fits under the limits."""
    def __init__(self, tpm: int, rpm: int):
        self.tpm = int(tpm * 0.9)  # keep 10% headroom for estimation error
        self.rpm = rpm
        self.events = deque()  # [timestamp, tokens]
        self.lock = threading.Lock()

    def acquire(self, tokens: int):
        tokens = min(tokens, self.tpm)
        while True:
            with self.lock:
                now = time.time()
                while self.events and now - self.events[0][0] > 60:
                    self.events.popleft()
                used = sum(t for _, t in self.events)
                if used + tokens <= self.tpm and len(self.events) < self.rpm:
                    event = [now, tokens]
                    self.events.append(event)
                    return event
                wait = 60 - (now - self.events[0][0]) + 0.5
            print(f"   ⏳ Rate-limit guard: waiting {wait:.0f}s for Groq token budget...")
            time.sleep(wait)

    def settle(self, event, actual_tokens: int):
        # Replace the up-front estimate with the real usage reported by Groq
        with self.lock:
            event[1] = actual_tokens

rate_guards = {
    FAST_MODEL: RateLimitGuard(GROQ_TPM_LIMIT, GROQ_RPM_LIMIT),
    CREATIVE_MODEL: RateLimitGuard(GROQ_TPM_LIMIT, GROQ_RPM_LIMIT),
}

def ask_llm(prompt: str, creative: bool = False, max_tokens: int = 1024, schema=None):
    """Calls Groq with rate-limit protection. Returns text, or a parsed `schema` instance if given."""
    model = CREATIVE_MODEL if creative else FAST_MODEL
    llm = ChatGroq(
        model=model,
        temperature=0.8 if creative else 0.5,
        max_tokens=max_tokens,
        reasoning_effort="low",  # reasoning tokens count against the TPM budget
        max_retries=4,           # groq client backs off on 429 using retry-after
    )
    # Groq reserves prompt + max_tokens against the TPM limit, so estimate the same way (~3.5 chars/token)
    event = rate_guards[model].acquire(int(len(prompt) / 3.5) + max_tokens)

    messages = [HumanMessage(content=prompt)]
    if schema:
        # Strict json_schema makes Groq constrain decoding to the schema (tool calling can drop fields).
        # langchain-groq doesn't send `strict`, so we build the response_format ourselves.
        json_schema = schema.model_json_schema()
        json_schema["additionalProperties"] = False
        structured = llm.bind(response_format={
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": json_schema, "strict": True},
        })
        for attempt in range(2):
            try:
                raw = structured.invoke(messages)
                output = schema.model_validate_json(raw.content)
                break
            except Exception as e:
                error = e
                print(f"   ⚠️ Structured output attempt {attempt + 1} failed: {str(e)[:150]}")
        else:
            raise ValueError(f"Structured output failed: {error}")
    else:
        raw = llm.invoke(messages)
        output = raw.content

    usage = getattr(raw, "usage_metadata", None)
    if usage:
        rate_guards[model].settle(event, usage.get("total_tokens", event[1]))
    return output

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
    q_result = ask_llm(f"""
        Today is {date.today():%B %d, %Y}. We are covering '{topic}'.
        Generate ONE highly effective KEYWORD search string to find breaking news.

        CRITICAL RULES:
        1. Output strictly keywords (e.g. "Stripe IPO valuation", NOT "What is Stripe's IPO valuation?").
        2. Use logical operators if needed (e.g. "Nvidia AND (AMD OR Intel)").
        3. Target a specific, recent event.
        """, max_tokens=600, schema=SearchQueries)
    
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
    {raw_data[:8000]}
    """
    summary = ask_llm(summary_prompt, creative=True, max_tokens=1500)
    
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
    
    # Use the Creative Model
    draft = ask_llm(prompt, creative=True, max_tokens=3500)

    return {"draft": draft, "revision_count": 0}

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
    
    # Use the Fast Model
    result = ask_llm(prompt, max_tokens=1200, schema=EditorOutput)
    
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
    
    # We use the Creative Model because rewriting requires high nuance to not lose the 'voice'
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
    
    refined = ask_llm(prompt, creative=True, max_tokens=3500)

    return {
        "draft": refined,
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
    
    # Use the Fast Model for this. It's great at following strict schemas.
    result = ask_llm(prompt, max_tokens=1500, schema=DistributionPackage)
    
    print(f"   [SEO] Viral Title: {result.title_viral}")
    
    # We save this as a dictionary to store in Firestore later
    return {
        "final_metadata": result.model_dump()
    }

# --- UPDATED STATE DEFINITION ---
# This matches the data output by your new advanced nodes and maps to the Firestore drafts collection
class AgentState(TypedDict):
    topic: str
    search_queries: List[str]   # Added for Researcher
    research_summary: str
    draft: str                  # Maps to draft_content / content_markdown
    critique: str               # Maps to critique_notes
    revision_count: int
    is_approved: bool
    score: int                  # Added for Editor
    viral_score: int            # For drafts
    sentiment: str              # For drafts
    target_audience: str        # For drafts
    reading_time_min: int       # For drafts
    seo_keywords: List[str]     # For drafts
    meta_description: str       # For drafts
    image_prompt: str           # For drafts
    final_metadata: dict        # Added for SEO

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
workflow.add_edge("seo", END)

# 7. Compile
app_graph = workflow.compile()