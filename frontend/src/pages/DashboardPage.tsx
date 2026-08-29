import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { meetingApi } from "../api/client";
import type { Meeting } from "../types";

export function DashboardPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    meetingApi
      .get<Meeting[]>("/meetings/")
      .then((res) => setMeetings(res.data))
      .catch(() => setMeetings([]))
      .finally(() => setLoading(false));
  }, []);

  const now = new Date();
  const planirani = meetings.filter(
    (m) => m.status === "PLANIRAN" && new Date(m.scheduled_at) >= now
  );
  const odrzani = meetings.filter((m) => m.status === "ODRZAN");

  if (loading) return <p>Učitavanje...</p>;

  return (
    <>
      <h2>Početna</h2>

      <div style={{ display: "flex", gap: "20px", marginBottom: "24px" }}>
        <div className="card" style={{ flex: 1 }}>
          <div style={{ fontSize: "13px", color: "#7f8c8d" }}>Ukupno sastanaka</div>
          <div style={{ fontSize: "32px", fontWeight: 700 }}>{meetings.length}</div>
        </div>
        <div className="card" style={{ flex: 1 }}>
          <div style={{ fontSize: "13px", color: "#7f8c8d" }}>Planirani</div>
          <div style={{ fontSize: "32px", fontWeight: 700, color: "#1976d2" }}>
            {planirani.length}
          </div>
        </div>
        <div className="card" style={{ flex: 1 }}>
          <div style={{ fontSize: "13px", color: "#7f8c8d" }}>Održani</div>
          <div style={{ fontSize: "32px", fontWeight: 700, color: "#388e3c" }}>
            {odrzani.length}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: "16px" }}>Predstojeći sastanci</h3>
        {planirani.length === 0 ? (
          <p style={{ color: "#7f8c8d" }}>Nema planiranih sastanaka.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Tema</th>
                <th>Datum</th>
                <th>Mesto</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {planirani.map((m) => (
                <tr key={m.id}>
                  <td>{m.topic}</td>
                  <td>{new Date(m.scheduled_at).toLocaleString("sr-RS")}</td>
                  <td>{m.location}, {m.room}</td>
                  <td>
                    <Link className="btn btn-sm" to={`/meetings/${m.id}`}>
                      Detalji
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}