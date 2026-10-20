# 🧠 AI Knowledge Inbox (Turium AI Full-Stack Design Assessment)

A production-ready, full-stack **RAG (Retrieval-Augmented Generation)** knowledge management system built as part of the Turium AI engineering assessment. The application allows users to ingest raw notes or web URLs, automatically chunks and vectorizes the content locally, performs high-speed semantic vector search using cosine similarity, and synthesizes accurate, cited answers using the Groq LLM inference engine.

---

## 🛠️ Tech Stack & Architecture

* **Frontend:** React, TypeScript, Modern CSS/Flexbox UI
* **Backend Microservice:** FastAPI (Python), Uvicorn, Pydantic
* **Vector Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`) running 100% locally on CPU (private, zero external API cost)
* **LLM Generation:** Groq API (`llama3-70b-8192`) for ultra-fast response synthesis
* **Web Scraping:** BeautifulSoup4 for clean text extraction from target URLs

---

## 📐 Design Decisions & Chunking Strategy

1. **Local Vectorization Strategy:** 
   To maintain data privacy and eliminate external API rate limits or costs for embedding generation, the system utilizes `sentence-transformers` locally. It maps sentences into a 384-dimensional dense vector space.
2. **Text Chunking Algorithm:** 
   Raw notes and scraped webpage text are broken down using a sliding window chunking strategy (`chunk_size = 400` characters with an `overlap = 50` characters). This ensures contextual continuity across chunk boundaries so semantic meaning isn't lost during retrieval.
3. **Similarity Search:** 
   User queries are vectorized on-the-fly and matched against stored chunks using NumPy-accelerated **Cosine Similarity**. The top 3 most relevant context chunks are injected into the Groq LLM prompt alongside strict source citation rules.

---

## 🚀 Local Development Setup

### 1. Backend Setup
Navigate to the backend directory, install dependencies, and run the server:
```bash
cd Backend
pip install -r requirements.txt
uvicorn main:app --reload