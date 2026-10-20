import React, { useState, useEffect, FC, FormEvent } from 'react';
import './App.css';

interface KnowledgeItem {
  id: number;
  title: string;
  type: string;
  source: string;
}

interface QueryResponse {
  answer: string;
  sources: string[];
}

const App: FC = () => {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [type, setType] = useState<string>('text');
  const [title, setTitle] = useState<string>('');
  const [content, setContent] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [answerData, setAnswerData] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const BACKEND_URL = 'https://turium-server-new.onrender.com';

  const fetchItems = async (): Promise<void> => {
    try {
      const res = await fetch(`${BACKEND_URL}/items`);
      const data: KnowledgeItem[] = await res.json();
      setItems(data);
    } catch (err) {
      console.error("Error fetching items:", err);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleIngest = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!title || !content) {
      alert("Please fill in all fields");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, title, content })
      });
      if (res.ok) {
        setTitle('');
        setContent('');
        fetchItems();
      }
    } catch (err) {
      alert("Error saving item");
    }
    setLoading(false);
  };

  const handleQuery = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!question) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data: QueryResponse = await res.json();
      setAnswerData(data);
    } catch (err) {
      alert("Error querying knowledge base");
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f8fafc", color: "#1e293b", fontFamily: "Inter, system-ui, sans-serif", padding: "40px 20px" }}>
      <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
        
        {/* Header */}
        <header style={{ textAlign: "center", marginBottom: "40px" }}>
          <h1 style={{ fontSize: "2.5rem", fontWeight: "800", color: "#0f172a", marginBottom: "10px" }}>🧠 AI Knowledge Inbox</h1>
          <p style={{ color: "#64748b", fontSize: "1.1rem" }}>Turium AI Full Stack Design Assessment (RAG Pipeline)</p>
        </header>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", alignItems: "start" }}>
          
          {/* Left Column: Ingestion Form */}
          <div style={{ background: "#ffffff", padding: "24px", borderRadius: "12px", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)", border: "1px solid #e2e8f0" }}>
            <h3 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "16px", color: "#334155" }}>📥 Ingest Knowledge</h3>
            <form onSubmit={handleIngest}>
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: "500", marginBottom: "6px" }}>Content Type</label>
                <select 
                  value={type} 
                  onChange={(e) => setType(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", background: "#fff" }}
                >
                  <option value="text">Plain Text Note</option>
                  <option value="url">Web URL Link</option>
                </select>
              </div>

              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: "500", marginBottom: "6px" }}>Title / Topic</label>
                <input 
                  type="text" 
                  placeholder="e.g., Project Architecture Overview" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)} 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", boxSizing: "border-box" }}
                />
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: "500", marginBottom: "6px" }}>Content / URL</label>
                <textarea 
                  placeholder={type === 'text' ? "Paste notes here..." : "https://example.com"} 
                  value={content} 
                  onChange={(e) => setContent(e.target.value)} 
                  rows={4}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", boxSizing: "border-box", resize: "vertical" }}
                />
              </div>

              <button 
                type="submit" 
                disabled={loading} 
                style={{ width: "100%", background: "#2563eb", color: "white", padding: "12px", borderRadius: "8px", border: "none", fontWeight: "600", cursor: "pointer", transition: "background 0.2s" }}
              >
                {loading ? "Processing Embeddings..." : "Save & Vectorize"}
              </button>
            </form>
          </div>

          {/* Right Column: Q&A / RAG Search */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            
            <div style={{ background: "#ffffff", padding: "24px", borderRadius: "12px", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)", border: "1px solid #e2e8f0" }}>
              <h3 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "16px", color: "#334155" }}>🔍 Ask AI (RAG Search)</h3>
              <form onSubmit={handleQuery}>
                <div style={{ marginBottom: "16px" }}>
                  <input 
                    type="text" 
                    placeholder="Ask a question about your stored items..." 
                    value={question} 
                    onChange={(e) => setQuestion(e.target.value)} 
                    style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", boxSizing: "border-box" }}
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={loading} 
                  style={{ width: "100%", background: "#059669", color: "white", padding: "12px", borderRadius: "8px", border: "none", fontWeight: "600", cursor: "pointer" }}
                >
                  {loading ? "Searching Knowledge..." : "Ask Question"}
                </button>
              </form>

              {answerData && (
                <div style={{ marginTop: "20px", background: "#f1f5f9", padding: "16px", borderRadius: "8px", borderLeft: "4px solid #059669" }}>
                  <h4 style={{ margin: "0 0 8px 0", fontSize: "1rem", color: "#0f172a" }}>Answer:</h4>
                  <p style={{ margin: "0 0 12px 0", lineHeight: "1.5", fontSize: "0.95rem" }}>{answerData.answer}</p>
                  <div style={{ fontSize: "0.8rem", color: "#64748b" }}>
                    <strong>Sources:</strong> {answerData.sources.join(", ") || "None"}
                  </div>
                </div>
              )}
            </div>

            {/* Saved Items Feed */}
            <div style={{ background: "#ffffff", padding: "20px", borderRadius: "12px", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)", border: "1px solid #e2e8f0", maxHeight: "250px", overflowY: "auto" }}>
              <h4 style={{ margin: "0 0 12px 0", fontSize: "1rem", color: "#334155" }}>📚 Saved Items Feed ({items.length})</h4>
              {items.length === 0 ? (
                <p style={{ fontSize: "0.875rem", color: "#94a3b8", margin: 0 }}>No items ingested yet.</p>
              ) : (
                <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
                  {items.map((item) => (
                    <li key={item.id} style={{ background: "#f8fafc", padding: "10px 12px", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "0.875rem" }}>
                      <span style={{ fontWeight: "600", color: "#2563eb", textTransform: "uppercase", fontSize: "0.75rem", marginRight: "6px", background: "#dbeafe", padding: "2px 6px", borderRadius: "4px" }}>
                        {item.type}
                      </span>
                      <strong>{item.title}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </div>

          </div>

        </div>

      </div>
    </div>
  );
};

export default App;