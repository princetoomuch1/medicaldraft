import { useState } from "react";
import axios from "../api/axiosConfig";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const response = await axios.post("/api/auth/login", { email, password });
      const token = response.data.access_token;
      localStorage.setItem("access_token", token);
      setMessage("Login successful");
    } catch (error) {
      console.error(error);
      setMessage("Login failed");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <label style={{ display: "block", marginBottom: 12 }}>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} style={{ width: "100%", marginTop: 4 }} />
        </label>
        <label style={{ display: "block", marginBottom: 12 }}>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} style={{ width: "100%", marginTop: 4 }} />
        </label>
        <button type="submit" style={{ marginTop: 12 }}>Sign in</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}
