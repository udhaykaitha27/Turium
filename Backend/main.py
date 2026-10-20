import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing in environment variables.")

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="AI Knowledge Inbox - Free Tier Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
ITEMS_DB = [
    {
        "id": 1,
        "title": "Turium AI Company Overview",
        "type": "text",
        "source": "Turium AI builds modern intelligent enterprise applications. It focuses on combining backend systems, async workflows, and RAG pipelines to deliver production-ready AI solutions."
    }
]

class IngestRequest(BaseModel):
    type: str  # "text" or "url"
    content: str
    title: str = "Untitled Note"

class QueryRequest(BaseModel):
    question: str

@app.post("/ingest")
def ingest_content(data: IngestRequest):
    raw_content = data.content
    title = data.title

    if data.type == "url":
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(data.content, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            raw_content = "\n".join(paragraphs)
            if not raw_content:
                raw_content = soup.get_text()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    item_id = len(ITEMS_DB) + 1
    item_record = {"id": item_id, "title": title, "type": data.type, "source": raw_content}
    ITEMS_DB.append(item_record)

    return {"message": "Content ingested successfully!", "item_id": item_id}

@app.get("/items")
def get_items():
    return ITEMS_DB

@app.post("/query")
def query_rag(data: QueryRequest):
    if not ITEMS_DB:
        return {"answer": "No knowledge items stored yet. Please add notes or URLs first.", "sources": []}

    # Find relevant items based on keyword matching
    query_words = set(data.question.lower().split())
    scored_items = []
    
    for item in ITEMS_DB:
        text = (item["title"] + " " + item["source"]).lower()
        score = sum(1 for word in query_words if word in text)
        scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    top_items = scored_items[:2] # Grab top 2 matching sources

    context_text = ""
    sources = []
    for score, item in top_items:
        context_text += f"\n---\nSource: {item['title']}\nContent: {item['source']}\n"
        if item['title'] not in sources:
            sources.append(item['title'])

    prompt = f"""
    You are an AI knowledge assistant. Answer the user's question accurately using ONLY the provided context below. If the answer cannot be found in the context, state that you don't know. Include citations to the sources.

    Context:
    {context_text}

    User Question: {data.question}
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a helpful RAG assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq LLM generation failed: {str(e)}")

    return {
        "answer": answer,
        "sources": sources
    }