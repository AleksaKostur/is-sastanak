import { useEffect, useState } from "react";
import { meetingApi } from "../api/client";
import { firstError, validateRequired } from "../utils/validation";
import { Pagination } from "../components/Pagination";
import type { ExternalPerson } from "../types";

export function ExternalPersonsPage() {
  const [people, setPeople] = useState<ExternalPerson[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  const [form, setForm] = useState({
    organization: "",
    first_name: "",
    last_name: "",
    job_title: "",
    country: "",
    rank: "",
  });

  const loadData = () => {
    setLoading(true);
    meetingApi
      .get<ExternalPerson[]>("/meetings/external-persons/list")
      .then((res) => setPeople(res.data))
      .catch(() => setError("Greška pri učitavanju"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const updateField = (field: string, value: string) => {
    setForm({ ...form, [field]: value });
  };

  const createPerson = async () => {
    setError("");
    const validationError = firstError(
      validateRequired(form.organization, "Organizacija"),
      validateRequired(form.first_name, "Ime"),
      validateRequired(form.last_name, "Prezime"),
    );
    if (validationError) {
      setError(validationError);
      return;
    }
    try {
      await meetingApi.post("/meetings/external-persons/create", form);
      setForm({ organization: "", first_name: "", last_name: "", job_title: "", country: "", rank: "" });
      setShowForm(false);
      loadData();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || "Greška pri kreiranju");
    }
  };

  if (loading) return <p>Učitavanje...</p>;

  const paginatedPeople = people.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Eksterna lica</h2>
        <button className="btn" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Otkaži" : "+ Novo lice"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {showForm && (
        <div className="card">
          <h3 style={{ marginBottom: "16px" }}>Novo eksterno lice</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label>Organizacija</label>
              <input value={form.organization} onChange={(e) => updateField("organization", e.target.value)} />
            </div>
            <div>
              <label>Zemlja</label>
              <input value={form.country} onChange={(e) => updateField("country", e.target.value)} />
            </div>
            <div>
              <label>Ime</label>
              <input value={form.first_name} onChange={(e) => updateField("first_name", e.target.value)} />
            </div>
            <div>
              <label>Prezime</label>
              <input value={form.last_name} onChange={(e) => updateField("last_name", e.target.value)} />
            </div>
            <div>
              <label>Radno mesto</label>
              <input value={form.job_title} onChange={(e) => updateField("job_title", e.target.value)} />
            </div>
            <div>
              <label>Čin</label>
              <input value={form.rank} onChange={(e) => updateField("rank", e.target.value)} />
            </div>
          </div>
          <button className="btn" style={{ marginTop: "16px" }} onClick={createPerson}>
            Sačuvaj
          </button>
        </div>
      )}

      <div className="card">
        {people.length === 0 ? (
          <p style={{ color: "#7f8c8d" }}>Nema evidentiranih eksternih lica.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Ime i prezime</th><th>Organizacija</th><th>Zemlja</th>
                <th>Radno mesto</th><th>Čin</th>
              </tr>
            </thead>
            <tbody>
              {paginatedPeople.map((p) => (
                <tr key={p.id}>
                  <td>{p.first_name} {p.last_name}</td>
                  <td>{p.organization}</td>
                  <td>{p.country || "-"}</td>
                  <td>{p.job_title || "-"}</td>
                  <td>{p.rank || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Pagination
          currentPage={currentPage}
          totalItems={people.length}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
        />
      </div>
    </>
  );
}