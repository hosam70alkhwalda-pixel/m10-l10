import { useState } from "react";
import { useRouter } from "next/router";
import { authFetch, API_URL } from "../lib/api";

interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
}

interface ExtractResponse {
  entities: Entity[];
}

export default function ExtractPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const res = await authFetch(`${API_URL}/extract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (res.status === 401) {
        router.push("/login");
        return;
      }

      if (res.status === 403) {
        setError("Insufficient scope — you don't have access to this resource.");
        return;
      }

      if (res.status === 422) {
        const detail = await res.json();
        setError(`Validation error: ${JSON.stringify(detail.detail)}`);
        return;
      }

      if (res.status === 503) {
        setError("Backend service is not ready. Please try again shortly.");
        return;
      }

      if (!res.ok) {
        setError(`Unexpected error (status ${res.status}).`);
        return;
      }

      const data: ExtractResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>Extract — Named Entity Recognition</h1>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={submit} disabled={!text || loading}>
        {loading ? "Extracting..." : "Extract"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <ul>
          {result.entities.map((ent, i) => (
            <li key={i} data-testid="entity-span">
              {ent.text} <em>({ent.label})</em>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}