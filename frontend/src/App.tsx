import { useMemo, useState, type FormEvent } from "react";
import { MapContainer, TileLayer, CircleMarker, useMapEvents } from "react-leaflet";
import { Link, Routes, Route } from "react-router-dom";
import axios from "./api/axiosConfig";
import { useMapData } from "./hooks/useMapData";
import HomePage from "./pages/Home";
import DashboardPage from "./pages/Dashboard";
import LoginPage from "./pages/Login";
import CaseDetailPage from "./pages/CaseDetail";
import "leaflet/dist/leaflet.css";

const center: [number, number] = [20.5937, 78.9629];

type CaseFormState = {
  hospital_id: string;
  diagnosis: string;
  severity: string;
  latitude: string;
  longitude: string;
};

function MapEvents({ onBoundsChange }: { onBoundsChange: (bounds: { west: number; south: number; east: number; north: number }) => void }) {
  useMapEvents({
    moveend(event) {
      const bounds = event.target.getBounds();
      onBoundsChange({
        west: bounds.getWest(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        north: bounds.getNorth(),
      });
    },
    zoomend(event) {
      const bounds = event.target.getBounds();
      onBoundsChange({
        west: bounds.getWest(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        north: bounds.getNorth(),
      });
    },
  });
  return null;
}

function App() {
  const [bounds, setBounds] = useState({ west: 68, south: 8, east: 98, north: 38 });
  const { data, loading } = useMapData(bounds);
  const [form, setForm] = useState<CaseFormState>({
    hospital_id: "00000000-0000-0000-0000-000000000001",
    diagnosis: "",
    severity: "moderate",
    latitude: "20.5937",
    longitude: "78.9629",
  });

  const markers = useMemo(() => {
    return data.map((item) => {
      const color = item.severity === "critical" ? "#e11d48" : "#f59e0b";
      return (
        <CircleMarker
          key={item.id}
          center={[Number(item.latitude), Number(item.longitude)]}
          radius={8}
          pathOptions={{ color, fillColor: color, fillOpacity: 0.8 }}
        />
      );
    });
  }, [data]);

  async function submitCase(event: FormEvent) {
    event.preventDefault();
    try {
      await axios.post("/api/cases", {
        hospital_id: form.hospital_id,
        diagnosis: form.diagnosis,
        severity: form.severity,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        is_confirmed: true,
      });
      alert("Case submitted");
    } catch (error) {
      console.error(error);
      alert("Submission failed");
    }
  }

  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/case/:id" element={<CaseDetailPage />} />
      <Route
        path="/*"
        element={
          <div style={{ padding: 20 }}>
            <h1>Page not found</h1>
            <p>
              Return <Link to="/">home</Link>.
            </p>
          </div>
        }
      />
    </Routes>
  );
}

export default App;
