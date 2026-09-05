import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { meetingApi, reportApi } from "../api/client";
import type { Meeting } from "../types";

export function DashboardPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<{weekly: number; monthly: number; yearly: number} | null>(null);

  useEffect(() => {
    meetingApi
      .get<Meeting[]>("/meetings/")
      .then((res) => setMeetings(res.data))
      .catch(() => setMeetings([]))
      .finally(() => setLoading(false));

      reportApi
      .get("/reports/attendance-summary/me")
      .then((res) => setSummary(res.data))
      .catch(() => {});
  }, []);

  const now = new Date();
  const planirani = meetings.filter(
    (m) => m.status === "PLANIRAN" && new Date(m.scheduled_at) >= now
  );
  const odrzani = meetings.filter((m) => m.status === "ODRZAN");

  const downloadReport = async (period: string) => {
    try {
      const res = await reportApi.get(
        `/reports/attendance-report?period=${period}&format=PDF`,
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `izvestaj_ucesca_${period.toLowerCase()}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // tiho
    }
  };

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

      {summary && (
        <div className="card">
          <h3 style={{ marginBottom: "16px" }}>Moje učešće na sastancima</h3>
          <div style={{ display: "flex", gap: "20px", marginBottom: "16px" }}>
            <div>
              <div style={{ fontSize: "13px", color: "#7f8c8d" }}>Ove nedelje</div>
              <div style={{ fontSize: "24px", fontWeight: 700 }}>{summary.weekly}</div>
            </div>
            <div>
              <div style={{ fontSize: "13px", color: "#7f8c8d" }}>Ovog meseca</div>
              <div style={{ fontSize: "24px", fontWeight: 700, color: "#1976d2" }}>{summary.monthly}</div>
            </div>
            <div>
              <div style={{ fontSize: "13px", color: "#7f8c8d" }}>Ove godine</div>
              <div style={{ fontSize: "24px", fontWeight: 700, color: "#388e3c" }}>{summary.yearly}</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-sm" onClick={() => downloadReport("MONTHLY")}>
              Mesečni izveštaj (PDF)
            </button>
            <button className="btn btn-sm" onClick={() => downloadReport("YEARLY")}>
              Godišnji izveštaj (PDF)
            </button>
          </div>
        </div>
      )}

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
              {planirani.slice(0, 5).map((m) => (
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