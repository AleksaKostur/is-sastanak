import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { meetingApi } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Meeting, MeetingCategory } from "../types";

const STATUS_BADGE: Record<string, string> = {
  PLANIRAN: "badge-planiran",
  ODRZAN: "badge-odrzan",
  ODLOZEN: "badge-odlozen",
  OTKAZAN: "badge-otkazan",
};

export function MeetingsPage() {
  const { hasRole } = useAuth();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [categories, setCategories] = useState<MeetingCategory[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);

  // polja forme
  const [topic, setTopic] = useState("");
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [meetingType, setMeetingType] = useState<"STALNI" | "VANREDNI">("VANREDNI");
  const [recurrence, setRecurrence] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [location, setLocation] = useState("");
  const [room, setRoom] = useState("");
  const [formError, setFormError] = useState("");

  const canCreate = hasRole("ADMIN", "RUKOVODILAC");

  const loadData = () => {
    setLoading(true);
    Promise.all([
      meetingApi.get<Meeting[]>("/meetings/"),
      meetingApi.get<MeetingCategory[]>("/meetings/categories"),
    ])
      .then(([m, c]) => {
        setMeetings(m.data);
        setCategories(c.data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async () => {
    setFormError("");
    try {
      await meetingApi.post("/meetings/", {
        topic,
        category_id: Number(categoryId),
        org_unit_id: 1, // pojednostavljeno — u praksi bi bio dropdown
        meeting_type: meetingType,
        recurrence: meetingType === "STALNI" ? recurrence : null,
        scheduled_at: scheduledAt,
        location,
        room,
      });
      // reset forme
      setTopic("");
      setCategoryId("");
      setScheduledAt("");
      setLocation("");
      setRoom("");
      setShowForm(false);
      loadData();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setFormError(
        Array.isArray(detail) ? detail[0]?.msg : detail || "Greška pri kreiranju"
      );
    }
  };

  if (loading) return <p>Učitavanje...</p>;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Sastanci</h2>
        {canCreate && (
          <button className="btn" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Otkaži" : "+ Novi sastanak"}
          </button>
        )}
      </div>

      {showForm && canCreate && (
        <div className="card">
          <h3 style={{ marginBottom: "16px" }}>Novi sastanak</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label>Tema</label>
              <input value={topic} onChange={(e) => setTopic(e.target.value)} />
            </div>
            <div>
              <label>Kategorija</label>
              <select value={categoryId} onChange={(e) => setCategoryId(Number(e.target.value))}>
                <option value="">-- izaberi --</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Tip</label>
              <select value={meetingType} onChange={(e) => setMeetingType(e.target.value as any)}>
                <option value="VANREDNI">Vanredni</option>
                <option value="STALNI">Stalni</option>
              </select>
            </div>
            {meetingType === "STALNI" && (
              <div>
                <label>Periodičnost</label>
                <select value={recurrence} onChange={(e) => setRecurrence(e.target.value)}>
                  <option value="">-- izaberi --</option>
                  <option value="DNEVNI">Dnevni</option>
                  <option value="NEDELJNI">Nedeljni</option>
                  <option value="MESECNI">Mesečni</option>
                  <option value="TROMESECNI">Tromesečni</option>
                  <option value="SESTOMESECNI">Šestomesečni</option>
                  <option value="GODISNJI">Godišnji</option>
                </select>
              </div>
            )}
            <div>
              <label>Datum i vreme</label>
              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
              />
            </div>
            <div>
              <label>Lokacija</label>
              <input value={location} onChange={(e) => setLocation(e.target.value)} />
            </div>
            <div>
              <label>Sala</label>
              <input value={room} onChange={(e) => setRoom(e.target.value)} />
            </div>
          </div>
          {formError && <div className="error">{formError}</div>}
          <button className="btn" style={{ marginTop: "16px" }} onClick={handleCreate}>
            Sačuvaj
          </button>
        </div>
      )}

      <div className="card">
        {meetings.length === 0 ? (
          <p style={{ color: "#7f8c8d" }}>Nema sastanaka.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Tema</th>
                <th>Tip</th>
                <th>Datum</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {meetings.map((m) => (
                <tr key={m.id}>
                  <td>{m.topic}</td>
                  <td>{m.meeting_type}</td>
                  <td>{new Date(m.scheduled_at).toLocaleString("sr-RS")}</td>
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