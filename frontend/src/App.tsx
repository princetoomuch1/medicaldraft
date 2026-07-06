import { useMemo, useState, type FormEvent } from "react";
import { MapContainer, TileLayer, CircleMarker, useMapEvents } from "react-leaflet";
import axios from "axios";
import { useMapData } from "./hooks/useMapData";
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
    <div style={{ height: "100vh", width: "100vw" }}>
      <MapContainer center={center} zoom={5} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapEvents onBoundsChange={setBounds} />
        {markers}
      </MapContainer>

      <div style={{ position: "absolute", top: 16, right: 16, zIndex: 1000, background: "white", padding: 16, borderRadius: 8, width: 280 }}>
        <h3 style={{ marginTop: 0 }}>Report Case</h3>
        <form onSubmit={submitCase}>
          <label style={{ display: "block", marginBottom: 8 }}>
            Diagnosis
            <input value={form.diagnosis} onChange={(e) => setForm({ ...form, diagnosis: e.target.value })} style={{ width: "100%", marginTop: 4 }} />
          </label>
          <label style={{ display: "block", marginBottom: 8 }}>
            Severity
            <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} style={{ width: "100%", marginTop: 4 }}>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="moderate">Moderate</option>
              <option value="low">Low</option>
            </select>
          </label>
          <label style={{ display: "block", marginBottom: 8 }}>
            Latitude
            <input value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} style={{ width: "100%", marginTop: 4 }} />
          </label>
          <label style={{ display: "block", marginBottom: 8 }}>
            Longitude
            <input value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} style={{ width: "100%", marginTop: 4 }} />
          </label>
          <button type="submit" style={{ width: "100%" }}>Submit Case</button>
        </form>
        {loading && <p>Loading cases…</p>}
      </div>
    </div>
  );
}

export default App;
