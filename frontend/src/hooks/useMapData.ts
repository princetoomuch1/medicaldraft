import { useEffect, useState } from "react";
import axios from "axios";

export function useMapData(bounds: { west: number; south: number; east: number; north: number }) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const bbox = `${bounds.west},${bounds.south},${bounds.east},${bounds.north}`;
        const response = await axios.get(`/api/cases?bbox=${bbox}`);
        const payload = response?.data;
        setData(
          Array.isArray(payload)
            ? payload
            : Array.isArray((payload as any)?.items)
            ? (payload as any).items
            : Array.isArray((payload as any)?.cases)
            ? (payload as any).cases
            : []
        );
      } catch (error) {
        console.error("Failed to fetch map data", error);
        setData([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => window.clearTimeout(timer);
  }, [bounds.west, bounds.south, bounds.east, bounds.north]);

  return { data, loading };
}
