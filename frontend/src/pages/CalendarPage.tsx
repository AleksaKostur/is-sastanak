import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { meetingApi } from "../api/client";
import type { Meeting } from "../types";

const STATUS_BADGE: Record<string, string> = {
  PLANIRAN: "badge-planiran",
  ODRZAN: "badge-odrzan",
  ODLOZEN: "badge-odlozen",
  OTKAZAN: "badge-otkazan",
};

export function CalendarPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  // filteri
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [status, setStatus] = useState("");
  const [meetingType, setMeetingType] = useState("");

  const loadMeetings = () => {
    setLoading(true);
    // sastavi query params od popunjenih filtera
    const params: Record<string, string> = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (status) params.status = status;
    if (meetingType) params.meeting_type = meetingType;

    meetingApi
      .get<Meeting[]>("/calendar/", { params })
      .then((res) => setMeetings(res.data))
      .catch(() => setMeetings([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadMeetings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetFilters = () => {
    setDateFrom("");
    setDateTo("");
    setStatus("");
    setMeetingType("");
    // učitaj sve nakon reseta
    setTimeout(loadMeetings, 0);
  };

  return (
    <>
      <h2>Kalendar sastanaka</h2>

      {/* Filteri */}
      <div className="card">
        <h3 style={{ marginBottom: "16px" }}>Filteri</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px" }}>
          <div>
            <label>Od datuma</label>
            <input
              type="datetime-local"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div>
            <label>Do datuma</label>
            <input
              type="datetime-local"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <div>
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Svi</option>
              <option value="PLANIRAN">Planiran</option>
              <option value="ODRZAN">Održan</option>
              <option value="ODLOZEN">Odložen</option>
              <option value="OTKAZAN">Otkazan</option>
            </select>
          </div>
          <div>
            <label>Tip</label>
            <select value={meetingType} onChange={(e) => setMeetingType(e.target.value)}>
              <option value="">Svi</option>
              <option value="STALNI">Stalni</option>
              <option value="VANREDNI">Vanredni</option>
            </select>
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
          <button className="btn" onClick={loadMeetings}>Primeni filtere</button>
          <button className="btn btn-sm" style={{ background: "#95a5a6" }} onClick={resetFilters}>
            Poništi
          </button>
        </div>
      </div>

      {/* Rezultati */}
      <div className="card">
        {loading ? (
          <p>Učitavanje...</p>
        ) : meetings.length === 0 ? (
          <p style={{ color: "#7f8c8d" }}>Nema sastanaka za izabrane filtere.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Tema</th><th>Tip</th><th>Datum</th><th>Mesto</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {meetings.map((m) => (
                <tr key={m.id}>
                  <td>{m.topic}</td>
                  <td>{m.meeting_type}</td>
                  <td>{new Date(m.scheduled_at).toLocaleString("sr-RS")}</td>
                  <td>{m.location}, {m.room}</td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[m.status]}`}>{m.status}</span>
                  </td>
                  <td>
                    <Link className="btn btn-sm" to={`/meetings/${m.id}`}>Detalji</Link>
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