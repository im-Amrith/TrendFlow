# TrendFlow 🚀

**TrendFlow** is an AI-powered content automation platform designed for tech bloggers and developers. It aggregates trending news, generates high-quality blog posts using advanced AI agents (LangGraph + Groq), and allows one-click publishing to Dev.to. Every service it uses has a free tier.

![TrendFlow Dashboard](https://via.placeholder.com/1200x600?text=TrendFlow+Dashboard+Preview)

## ✨ Features

*   **🤖 AI Agent Workflow**: Uses a multi-step LangGraph workflow (Research -> Draft -> Critique -> SEO -> Polish) to generate professional-grade content.
*   **📰 Smart News Aggregation**: Fetches trending topics from GNews, NewsData, and Google News to keep your content fresh.
*   **🔐 Multi-User Isolation**: Google sign-in via Firebase Auth, with per-user data isolation in Firestore.
*   **📢 Multi-Platform Publishing**: One-click publishing to **Dev.to**.
*   **📊 Analytics Dashboard**: Track views, reactions, and comments across all your published posts in one place.
*   **🎨 Modern UI**: Built with React, Tailwind CSS, and Three.js for a fluid and responsive experience.

## 🛠️ Tech Stack

### Frontend
*   **Framework**: React (Vite)
*   **Styling**: Tailwind CSS, Lucide React
*   **Visuals**: Three.js (React Three Fiber)
*   **Auth**: Firebase Authentication (Google sign-in)

### Backend
*   **API**: FastAPI (Python)
*   **AI Orchestration**: LangGraph, LangChain
*   **LLM**: Groq free tier (`openai/gpt-oss-120b` for writing, `openai/gpt-oss-20b` for structured steps), with a built-in token-per-minute rate-limit guard
*   **Database**: Firebase Firestore
*   **News Sources**: GNews, MarketAux, NYT, NewsData, The Guardian, Google News scraper, DuckDuckGo

---

## 🚀 Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python (v3.11+)
*   Firebase project (Authentication with Google provider + Firestore) and a service-account key
*   API Keys (Groq, GNews, etc.)

### 1. Clone the Repository
```bash
git clone https://github.com/im-Amrith/TrendFlow.git
cd TrendFlow
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run the server (put your service-account key at backend/firebase-key.json)
cd backend
uvicorn main:app --reload
```
The backend will run at `http://localhost:8000`.

### 3. Frontend Setup
```bash
# Install dependencies
npm install

# Run the development server
npm run dev
```
The frontend will run at `http://localhost:3000`.

---

## 🌍 Deployment

### Backend (Hugging Face Spaces)
We use **Docker** to deploy the FastAPI backend on Hugging Face Spaces.

1.  Create a new **Space** on Hugging Face.
2.  Select **Docker** as the SDK.
3.  Upload the contents of this repository (or connect your GitHub repo).
4.  **Important**: Go to **Settings** -> **Variables and secrets** in your Space and add the following secrets (from your `.env.local`):
    *   `FIREBASE_SERVICE_ACCOUNT` (the full contents of your Firebase service-account JSON)
    *   `GROQ_API_KEY`
    *   `GNEWS_API_KEY`, `MARKETAUX_API_KEY`, `NYT_API_KEY`, `NEWSDATA_API_KEY`, `GUARDIAN_API_KEY` (each optional; missing sources are skipped)

The Space will build the Docker image and expose the API. Note the **Direct URL** of your Space (e.g., `https://huggingface.co/spaces/username/space-name`).

### Frontend (Vercel)
1.  Push your code to GitHub.
2.  Import the project into **Vercel**.
3.  Vercel will auto-detect Vite.
4.  Add the following **Environment Variables** in Vercel:
    *   `VITE_API_URL`: The URL of your Hugging Face Space (e.g., `https://username-space-name.hf.space`). **Note**: Ensure you use the direct URL without the iframe.

5.  In the Firebase console, add your Vercel domain under **Authentication -> Settings -> Authorized domains**.

6.  Deploy! 🚀

---

## 🔑 Environment Variables

Create `backend/.env` for local development (the frontend only needs `VITE_API_URL`, which defaults to `http://localhost:8000`):

```env
# Backend
GROQ_API_KEY=your_groq_key
GOOGLE_APPLICATION_CREDENTIALS=firebase-key.json

# News APIs (each optional)
GNEWS_API_KEY=your_key
MARKETAUX_API_KEY=your_key
NYT_API_KEY=your_key
NEWSDATA_API_KEY=your_key
GUARDIAN_API_KEY=your_key
```

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
[MIT](https://choosealicense.com/licenses/mit/)
