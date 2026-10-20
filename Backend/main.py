import os
import sqlite3
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing in environment variables.")

client = Groq(api_key=GROQ_API_KEY)
print("Loading local embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully!")

app = FastAPI(title="AI Knowledge Inbox - Groq Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_ITEMS = [
    {
        "id": 1,
        "title": "Turium AI Company Overview",
        "type": "text",
        "source": "Turium AI builds modern intelligent enterprise applications. It focuses on combining backend systems, async workflows, and RAG (Retrieval-Augmented Generation) pipelines to deliver production-ready AI solutions."
    }
]

DATABASE_PATH = Path(__file__).resolve().with_name("knowledge.db")


def load_items():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                source TEXT NOT NULL
            )
            """
        )
        item_count = connection.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        if item_count == 0:
            connection.executemany(
                "INSERT INTO items (id, title, type, source) VALUES (?, ?, ?, ?)",
                [
                    (item["id"], item["title"], item["type"], item["source"])
                    for item in DEFAULT_ITEMS
                ],
            )
        rows = connection.execute(
            "SELECT id, title, type, source FROM items ORDER BY id"
        ).fetchall()

    return [
        {"id": row[0], "title": row[1], "type": row[2], "source": row[3]}
        for row in rows
    ]


ITEMS_DB = load_items()
CHUNKS_DB = []

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# Automatically vectorize default items on startup
def reindex_all():
    CHUNKS_DB.clear()
    for item in ITEMS_DB:
        chunks = chunk_text(item["source"])
        for chunk in chunks:
            vector = embedder.encode(chunk)
            CHUNKS_DB.append({
                "item_id": item["id"],
                "title": item["title"],
                "chunk": chunk,
                "vector": vector
            })
    print(f"Reindexed {len(CHUNKS_DB)} chunks into memory.")

reindex_all()

class IngestRequest(BaseModel):
    type: str
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

    text_chunks = chunk_text(raw_content)
    vectorized_chunks = [
        (chunk, embedder.encode(chunk))
        for chunk in text_chunks
    ]

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO items (title, type, source) VALUES (?, ?, ?)",
            (title, data.type, raw_content),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to save the ingested item.")
        item_id = cursor.lastrowid

    item_record = {"id": item_id, "title": title, "type": data.type, "source": raw_content}
    ITEMS_DB.append(item_record)
    for chunk, vector in vectorized_chunks:
        CHUNKS_DB.append({
            "item_id": item_id,
            "title": title,
            "chunk": chunk,
            "vector": vector
        })

    return {"message": "Content ingested and vectorized successfully!", "item_id": item_id}

@app.get("/items")
def get_items():
    return ITEMS_DB

@app.post("/query")
def query_rag(data: QueryRequest):
    print(f"\n--- Query Received: {data.question} ---")
    print(f"Total chunks available in search index: {len(CHUNKS_DB)}")

    if not CHUNKS_DB:
        reindex_all()

    if not CHUNKS_DB:
        return {"answer": "No knowledge items stored yet. Please add notes or URLs first.", "sources": []}

    try:
        q_vector = embedder.encode(data.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    scored_chunks = []
    for entry in CHUNKS_DB:
        v = entry["vector"]
        similarity = np.dot(q_vector, v) / (np.linalg.norm(q_vector) * np.linalg.norm(v))
        scored_chunks.append((similarity, entry))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored_chunks[:3]

    context_text = ""
    sources = []
    for score, item in top_chunks:
        context_text += f"\n---\nSource: {item['title']}\nContent: {item['chunk']}\n"
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
            model=GROQ_MODEL,
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

    if not isinstance(answer, str) or not answer.strip():
        raise HTTPException(
            status_code=502,
            detail="The language model returned an empty answer. Please retry the query.",
        )

    return {
        "answer": answer,
        "sources": sources
    }