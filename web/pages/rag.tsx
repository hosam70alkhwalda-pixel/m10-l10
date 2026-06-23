import { useState } from "react";
import { RAGResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RagPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/rag/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, k: 4 }),
      });
      if (res.status === 422) {
        const data = await res.json();
        setError(JSON.stringify(data.detail));
      } else if (res.status === 503) {
        setError("The backend is starting up — please try again in a moment.");
      } else if (!res.ok) {
        setError("Could not reach the backend.");
      } else {
        const data: RAGResponse = await res.json();
        setResult(data);
      }
    } catch {
      setError("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>RAG — Cited Answer</h1>
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a recipe question..."
      />
      <button onClick={submit} disabled={!question || loading}>
        {loading ? "Loading..." : "Ask"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {result && (
        <div>
          <p>{result.answer}</p>
          <div>
            {result.citations.map((c, i) => (
              <span key={i} data-testid="citation-marker">
                [{i + 1}] chunk_id: {c.chunk_id}, score: {c.score.toFixed(3)}
              </span>
            ))}
          </div>
          <p>Confidence: {result.confidence.toFixed(3)}</p>
        </div>
      )}
    </main>
  );
}