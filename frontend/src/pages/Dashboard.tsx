import { useEffect, useState } from "react";
import axios from "../api/axiosConfig";

type CaseSummary = {
  id: string;
  hospital_id: string | null;
  reported_at: string;
  diagnosis: string;
  severity: string;
  latitude: number;
  longitude: number;
  is_confirmed: boolean;
};

export default function DashboardPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const response = await axios.get("/api/cases?bbox=68,8,98,38&limit=50");
        setCases(response.data.items || []);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>Dashboard</h1>
      <p>Live case feed</p>
      {loading ? (
        <div>Loading…</div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>ID</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Diagnosis</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Severity</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Reported</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((item) => (
              <tr key={item.id}>
                <td style={{ padding: "8px 0" }}>{item.id}</td>
                <td style={{ padding: "8px 0" }}>{item.diagnosis}</td>
                <td style={{ padding: "8px 0" }}>{item.severity}</td>
                <td style={{ padding: "8px 0" }}>{new Date(item.reported_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
