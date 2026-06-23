import { useState } from "react";
import { useRouter } from "next/router";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (res.status === 401) {
        setError("Invalid username or password.");
      } else if (res.status === 503) {
        setError("The backend is starting up — please try again in a moment.");
      } else if (!res.ok) {
        setError("Could not reach the backend.");
      } else {
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        router.push("/extract");
      }
    } catch {
      setError("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>Login</h1>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={handleSubmit} disabled={!username || !password || loading}>
        {loading ? "Logging in..." : "Login"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </main>
  );
}