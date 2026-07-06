import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "../api/axiosConfig";

type CaseDetail = {
  id: string;
  hospital_id: string | null;
  reported_at: string;
  diagnosis: string;
  severity: string;
  latitude: number;
  longitude: number;
  is_confirmed: boolean;
};

type AuditItem = {
  id: string;
  case_id: string;
  changed_field: string;
  old_value: string | null;
  new_value: string | null;
  changed_at: string;
  changed_by: string | null;
};

export default function CaseDetailPage() {
  const { id } = useParams();
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [history, setHistory] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const load = async () => {
      setLoading(true);
      try {
        const [caseResp, historyResp] = await Promise.all([
          axios.get(`/api/cases/${id}`),
          axios.get(`/api/cases/${id}/history`),
        ]);
        setCaseDetail(caseResp.data);
        setHistory(historyResp.data);
      } catch (err) {
        console.error(err);
        setError("Unable to load case details.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [id]);

  if (loading) {
    return <div>Loading case details…</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  if (!caseDetail) {
    return <div>Case not found.</div>;
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Case detail</h1>
      <div style={{ marginBottom: 20 }}>
        <strong>Diagnosis:</strong> {caseDetail.diagnosis}
        <br />
        <strong>Severity:</strong> {caseDetail.severity}
        <br />
        <strong>Confirmed:</strong> {caseDetail.is_confirmed ? "Yes" : "No"}
        <br />
        <strong>Hospital ID:</strong> {caseDetail.hospital_id ?? "None"}
        <br />
        <strong>Reported:</strong> {new Date(caseDetail.reported_at).toLocaleString()}
        <br />
        <strong>Location:</strong> {caseDetail.latitude}, {caseDetail.longitude}
      </div>

      <h2>Audit history</h2>
      {history.length === 0 ? (
        <p>No edits recorded.</p>
      ) : (
        <ul>
          {history.map((item) => (
            <li key={item.id} style={{ marginBottom: 12 }}>
              <strong>{item.changed_field}</strong> changed from "{item.old_value ?? "—"}" to "{item.new_value ?? "—"}" by {item.changed_by ?? "unknown"} on {new Date(item.changed_at).toLocaleString()}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
