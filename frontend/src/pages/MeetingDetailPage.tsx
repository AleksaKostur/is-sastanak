import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { meetingApi, reportApi } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Meeting, AgendaItem, Participant, User } from "../types";

export function MeetingDetailPage() {
  const { id } = useParams();
  const meetingId = Number(id);
  const navigate = useNavigate();
  const { hasRole, userId } = useAuth();

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [agenda, setAgenda] = useState<AgendaItem[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [participantError, setParticipantError] = useState("");

  // forme
  const [newItemTitle, setNewItemTitle] = useState("");
  const [newItemOrder, setNewItemOrder] = useState<number | "">("");
  const [selectedUserId, setSelectedUserId] = useState<number | "">("");
  const [selectedRole, setSelectedRole] = useState("UCESNIK");

  const isOrganizer = meeting?.organizer_id === userId;
  const canManage = isOrganizer || hasRole("ADMIN");
  const canRecord = hasRole("ADMIN", "RUKOVODILAC", "ZAPISNICAR");

  const loadAll = () => {
    setLoading(true);
    Promise.all([
      meetingApi.get<Meeting>(`/meetings/${meetingId}`),
      meetingApi.get<AgendaItem[]>(`/meetings/${meetingId}/agenda`),
      meetingApi.get<Participant[]>(`/meetings/${meetingId}/participants`),
    ])
      .then(([m, a, p]) => {
        setMeeting(m.data);
        setAgenda(a.data);
        setParticipants(p.data);
      })
      .catch(() => setError("Greška pri učitavanju sastanka"))
      .finally(() => setLoading(false));

    // korisnici za dropdown (samo admin/rukovodilac mogu listati)
    if (hasRole("ADMIN", "RUKOVODILAC")) {
      meetingApi.get<User[]>("/../").catch(() => {}); // placeholder
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meetingId]);

  // ── akcije ──────────────────────────────────────────────────────────
  const addAgendaItem = async () => {
    setError("");
    try {
      await meetingApi.post(`/meetings/${meetingId}/agenda`, {
        order_no: Number(newItemOrder),
        title: newItemTitle,
      });
      setNewItemTitle("");
      setNewItemOrder("");
      loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Greška pri dodavanju stavke");
    }
  };

  const addParticipant = async () => {
    setParticipantError("");
    try {
      await meetingApi.post(`/meetings/${meetingId}/participants`, {
        user_id: Number(selectedUserId),
        role_in_meeting: selectedRole,
      });
      setSelectedUserId("");
      loadAll();
    } catch (err: any) {
      setParticipantError(err.response?.data?.detail || "Greška pri dodavanju učesnika");
    }
  };

  const recordAttendance = async (participantId: number, attended: boolean) => {
    setParticipantError("");
    try {
      await meetingApi.patch(
        `/meetings/${meetingId}/participants/${participantId}/attendance`,
        { attended }
      );
      loadAll();
    } catch (err: any) {
      setParticipantError(err.response?.data?.detail || "Greška pri evidenciji");
    }
  };

  const changeStatus = async (status: string) => {
    let reason = "";
    if (status === "ODLOZEN" || status === "OTKAZAN") {
      reason = prompt("Razlog:") || "";
      if (!reason) return;
    }
    try {
      await meetingApi.patch(`/meetings/${meetingId}/status`, {
        status,
        status_reason: reason || null,
      });
      loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Greška pri promeni statusa");
    }
  };

  const exportReport = async (format: string) => {
    try {
      const res = await reportApi.get(
        `/reports/meeting/${meetingId}/export?format=${format}`,
        { responseType: "blob" }
      );
      // napravi download link iz blob-a
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `zapisnik_sastanak_${meetingId}.${format.toLowerCase()}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Greška pri generisanju izveštaja");
    }
  };

  if (loading) return <p>Učitavanje...</p>;
  if (!meeting) return <p>Sastanak nije pronađen.</p>;

  return (
    <>
      <button className="btn btn-sm" onClick={() => navigate("/meetings")}>
        ← Nazad
      </button>

      {/* ── Osnovni podaci ── */}
      <div className="card" style={{ marginTop: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <h2>{meeting.topic}</h2>
          <span className={`badge badge-${meeting.status.toLowerCase()}`}>
            {meeting.status}
          </span>
        </div>
        <table style={{ marginTop: "16px" }}>
          <tbody>
            <tr><td><b>Tip</b></td><td>{meeting.meeting_type}</td></tr>
            <tr><td><b>Zakazano</b></td><td>{new Date(meeting.scheduled_at).toLocaleString("sr-RS")}</td></tr>
            <tr><td><b>Mesto</b></td><td>{meeting.location}, {meeting.room}</td></tr>
            {meeting.status_reason && (
              <tr><td><b>Razlog</b></td><td>{meeting.status_reason}</td></tr>
            )}
          </tbody>
        </table>

        {canManage && meeting.status === "PLANIRAN" && (
          <div style={{ marginTop: "16px", display: "flex", gap: "8px" }}>
            <button className="btn btn-sm btn-danger" onClick={() => changeStatus("OTKAZAN")}>
              Otkaži
            </button>
            <button className="btn btn-sm btn-odlozen" onClick={() => changeStatus("ODLOZEN")}
                    style={{ background: "#f57c00" }}>
              Odloži
            </button>
          </div>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {/* ── Dnevni red ── */}
      <div className="card">
        <h3 style={{ marginBottom: "16px" }}>Dnevni red</h3>
        {agenda.length === 0 ? (
          <p style={{ color: "#7f8c8d" }}>Nema stavki dnevnog reda.</p>
        ) : (
          <table>
            <thead>
              <tr><th>#</th><th>Naslov</th><th>Diskusija</th></tr>
            </thead>
            <tbody>
              {agenda.map((item) => (
                <tr key={item.id}>
                  <td>{item.order_no}</td>
                  <td>{item.title}</td>
                  <td>{item.discussion || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {canManage && meeting.status === "PLANIRAN" && (
          <div style={{ display: "flex", gap: "8px", marginTop: "16px", alignItems: "flex-end" }}>
            <div style={{ width: "80px" }}>
              <label>Rb.</label>
              <input type="number" value={newItemOrder}
                     onChange={(e) => setNewItemOrder(Number(e.target.value))} />
            </div>
            <div style={{ flex: 1 }}>
              <label>Naslov stavke</label>
              <input value={newItemTitle} onChange={(e) => setNewItemTitle(e.target.value)} />
            </div>
            <button className="btn" onClick={addAgendaItem}>Dodaj</button>
          </div>
        )}
      </div>

      {/* ── Učesnici ── */}
      <div className="card">
        <h3 style={{ marginBottom: "16px" }}>Učesnici</h3>
        {participantError && <div className="error">{participantError}</div>}
        {participants.length === 0 ? (
          <p style={{ color: "#7f8c8d" }}>Nema učesnika.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID korisnika</th><th>Uloga</th><th>Prisustvo</th>
                {canRecord && <th>Evidencija</th>}
              </tr>
            </thead>
            <tbody>
              {participants.map((p) => (
                <tr key={p.id}>
                  <td>{p.user_id ?? `ext:${p.external_person_id}`}</td>
                  <td>{p.role_in_meeting}</td>
                  <td>
                    {p.attended === null ? "-" : p.attended ? "Prisutan" : "Odsutan"}
                  </td>
                  {canRecord && (
                    <td>
                      <button className="btn btn-sm btn-success"
                              onClick={() => recordAttendance(p.id, true)}>✓</button>
                      {" "}
                      <button className="btn btn-sm btn-danger"
                              onClick={() => recordAttendance(p.id, false)}>✗</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {canManage && meeting.status === "PLANIRAN" && (
          <div style={{ display: "flex", gap: "8px", marginTop: "16px", alignItems: "flex-end" }}>
            <div style={{ width: "140px" }}>
              <label>ID korisnika</label>
              <input type="number" value={selectedUserId}
                     onChange={(e) => setSelectedUserId(Number(e.target.value))} />
            </div>
            <div style={{ width: "160px" }}>
              <label>Uloga</label>
              <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)}>
                <option value="UCESNIK">Učesnik</option>
                <option value="ZAPISNICAR">Zapisničar</option>
                <option value="RUKOVODILAC">Rukovodilac</option>
              </select>
            </div>
            <button className="btn" onClick={addParticipant}>Dodaj</button>
          </div>
        )}
      </div>

      {/* ── Izveštaji ── */}
      <div className="card">
        <h3 style={{ marginBottom: "16px" }}>Izveštaji</h3>
        <div style={{ display: "flex", gap: "8px" }}>
          <button className="btn" onClick={() => exportReport("PDF")}>PDF</button>
          <button className="btn" onClick={() => exportReport("XLSX")}>XLSX</button>
          <button className="btn" onClick={() => exportReport("DOCX")}>DOCX</button>
        </div>
      </div>
    </>
  );
}