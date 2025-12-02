import os
import requests
from dotenv import load_dotenv
from gnews import GNews
from duckduckgo_search import DDGS

# Load environment variables
load_dotenv()

# --- COLORS FOR TERMINAL OUTPUT ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

TEST_TOPIC = "Artificial Intelligence"

def print_status(source, status, message):
    if status == "SUCCESS":
        print(f"[{source}] {GREEN}✅ SUCCESS{RESET}: {message}")
    elif status == "FAIL":
        print(f"[{source}] {RED}❌ FAILED{RESET}: {message}")
    elif status == "SKIP":
        print(f"[{source}] {YELLOW}⏭️ SKIPPED{RESET}: {message}")

print(f"\n🔍 --- STARTING SOURCE CONNECTIVITY TEST FOR TOPIC: '{TEST_TOPIC}' ---\n")

# ---------------------------------------------------------
# 1. GNews API (Official)
# ---------------------------------------------------------
api_key = os.getenv("GNEWS_API_KEY")
if api_key:
    try:
        url = f"https://gnews.io/api/v4/search?q={TEST_TOPIC}&lang=en&max=3&apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('articles', []))
            if count > 0:
                print_status("GNews API", "SUCCESS", f"Found {count} articles. First: {data['articles'][0]['title'][:30]}...")
            else:
                print_status("GNews API", "FAIL", "API connected but returned 0 articles.")
        else:
            print_status("GNews API", "FAIL", f"Status Code {response.status_code} - {response.text}")
    except Exception as e:
        print_status("GNews API", "FAIL", str(e))
else:
    print_status("GNews API", "SKIP", "No GNEWS_API_KEY in .env")

# ---------------------------------------------------------
# 2. MarketAux
# ---------------------------------------------------------
api_key = os.getenv("MARKETAUX_API_KEY")
if api_key:
    try:
        url = f"https://api.marketaux.com/v1/news/all?search={TEST_TOPIC}&language=en&limit=2&api_token={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('data', []))
            if count > 0:
                # Test the entity sentiment bug fix logic
                first_art = data['data'][0]
                entities = first_art.get('entities', [])
                sentiment = entities[0].get('sentiment_score', 'N/A') if entities else "N/A"
                print_status("MarketAux", "SUCCESS", f"Found {count} articles. Sentiment extracted: {sentiment}")
            else:
                print_status("MarketAux", "FAIL", "API connected but returned 0 articles.")
        else:
            print_status("MarketAux", "FAIL", f"Status Code {response.status_code} - {response.text}")
    except Exception as e:
        print_status("MarketAux", "FAIL", str(e))
else:
    print_status("MarketAux", "SKIP", "No MARKETAUX_API_KEY in .env")

# ---------------------------------------------------------
# 3. New York Times (Debug Mode)
# ---------------------------------------------------------
api_key = os.getenv("NYT_API_KEY")
if api_key:
    try:
        params = {
            "q": TEST_TOPIC,
            "sort": "newest",
            "fq": 'section_name:("Technology" "Business")',
            "api-key": api_key
        }
        response = requests.get("https://api.nytimes.com/svc/search/v2/articlesearch.json", params=params)
        
        if response.status_code == 200:
            data = response.json()
            # SAFER HANDLING: Handle cases where 'response' or 'docs' might be missing
            response_body = data.get('response', {})
            if response_body is None: response_body = {}
            
            docs = response_body.get('docs')
            if docs is None: docs = [] # Fix for NoneType error
            
            if len(docs) > 0:
                headline = docs[0].get('headline', {}).get('main', 'No Title')
                print_status("NYT API", "SUCCESS", f"Found {len(docs)} articles. First: {headline[:30]}...")
            else:
                print_status("NYT API", "FAIL", f"Returned 0 docs. Raw Data: {data}")
        else:
            # Print the actual error message from NYT
            print_status("NYT API", "FAIL", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        print_status("NYT API", "FAIL", str(e))
else:
    print_status("NYT API", "SKIP", "No NYT_API_KEY in .env")

# ---------------------------------------------------------
# 4. NewsData.io
# ---------------------------------------------------------
api_key = os.getenv("NEWSDATA_API_KEY")
if api_key:
    try:
        url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={TEST_TOPIC}&language=en"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if len(results) > 0:
                print_status("NewsData", "SUCCESS", f"Found {len(results)} articles. First: {results[0]['title'][:30]}...")
            else:
                print_status("NewsData", "FAIL", "API connected but returned 0 results.")
        else:
            print_status("NewsData", "FAIL", f"Status Code {response.status_code} - {response.text}")
    except Exception as e:
        print_status("NewsData", "FAIL", str(e))
else:
    print_status("NewsData", "SKIP", "No NEWSDATA_API_KEY in .env")

# ---------------------------------------------------------
# 5. The Guardian
# ---------------------------------------------------------
api_key = os.getenv("GUARDIAN_API_KEY")
if api_key:
    try:
        url = f"https://content.guardianapis.com/search?q={TEST_TOPIC}&api-key={api_key}&show-fields=trailText"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            results = data.get('response', {}).get('results', [])
            if len(results) > 0:
                print_status("Guardian", "SUCCESS", f"Found {len(results)} articles. First: {results[0]['webTitle'][:30]}...")
            else:
                print_status("Guardian", "FAIL", "API connected but returned 0 results.")
        else:
            print_status("Guardian", "FAIL", f"Status Code {response.status_code}")
    except Exception as e:
        print_status("Guardian", "FAIL", str(e))
else:
    print_status("Guardian", "SKIP", "No GUARDIAN_API_KEY in .env")

# ---------------------------------------------------------
# 6. Google News (Library)
# ---------------------------------------------------------
try:
    google_news = GNews(max_results=3, period='12h') # Testing the 'freshness' param
    g_results = google_news.get_news(TEST_TOPIC)
    if len(g_results) > 0:
        print_status("Google News", "SUCCESS", f"Found {len(g_results)} articles via Scraper. First: {g_results[0]['title'][:30]}...")
    else:
        print_status("Google News", "FAIL", "Scraper worked but found 0 results (might be rate limited).")
except Exception as e:
    print_status("Google News", "FAIL", str(e))

# ---------------------------------------------------------
# 7. DuckDuckGo (Library)
# ---------------------------------------------------------
try:
    with DDGS() as ddgs:
        results = list(ddgs.text(keywords=f"{TEST_TOPIC} news", region="wt-wt", safesearch="off", timelimit="w", max_results=3))
        if len(results) > 0:
            print_status("DuckDuckGo", "SUCCESS", f"Found {len(results)} results. First: {results[0]['title'][:30]}...")
        else:
            print_status("DuckDuckGo", "FAIL", "Returned 0 results.")
except Exception as e:
    print_status("DuckDuckGo", "FAIL", str(e))

print("\n--- TEST COMPLETE ---\n")