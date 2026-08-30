import { useEffect, useState } from "react";
import { authApi } from "../api/client";
import type { User } from "../types";

interface Role {
  id: number;
  name: string;
}

export function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  // forma za novog korisnika
  const [form, setForm] = useState({
    first_name: "",
    father_name: "",
    last_name: "",
    jmbg: "",
    job_title: "",
    email: "",
    password: "",
    org_unit_id: 1,
  });

  // dodela uloge
  const [roleAssign, setRoleAssign] = useState<{ userId: number | ""; roleId: number | "" }>({
    userId: "",
    roleId: "",
  });

  const loadData = () => {
    setLoading(true);
    Promise.all([
      authApi.get<User[]>("/users/"),
      authApi.get<Role[]>("/roles/"),
    ])
      .then(([u, r]) => {
        setUsers(u.data);
        setRoles(r.data);
      })
      .catch(() => setError("Greška pri učitavanju"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const createUser = async () => {
    setError("");
    try {
      await authApi.post("/users/", form);
      setForm({
        first_name: "", father_name: "", last_name: "", jmbg: "",
        job_title: "", email: "", password: "", org_unit_id: 1,
      });
      setShowForm(false);
      loadData();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || "Greška pri kreiranju");
    }
  };

  const deactivateUser = async (userId: number) => {
    if (!confirm("Deaktivirati korisnika?")) return;
    try {
      await authApi.delete(`/users/${userId}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Greška pri deaktivaciji");
    }
  };

  const assignRole = async () => {
    setError("");
    if (!roleAssign.userId || !roleAssign.roleId) {
      setError("Izaberite korisnika i ulogu");
      return;
    }
    const role = roles.find((r) => r.id === roleAssign.roleId);
    const body: any = {
      user_id: roleAssign.userId,
      role_id: roleAssign.roleId,
      is_permanent: true,
    };
    // rukovodilac zahteva org_unit_id
    if (role?.name === "RUKOVODILAC") {
      body.org_unit_id = 1;
    }
    try {
      await authApi.post("/roles/assign", body);
      setRoleAssign({ userId: "", roleId: "" });
      setError("");
      alert("Uloga dodeljena");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Greška pri dodeli uloge");
    }
  };

  const updateField = (field: string, value: string | number) => {
    setForm({ ...form, [field]: value });
  };

  if (loading) return <p>Učitavanje...</p>;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Korisnici</h2>
        <button className="btn" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Otkaži" : "+ Novi korisnik"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {showForm && (
        <div className="card">
          <h3 style={{ marginBottom: "16px" }}>Novi korisnik</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label>Ime</label>
              <input value={form.first_name} onChange={(e) => updateField("first_name", e.target.value)} />
            </div>
            <div>
              <label>Ime oca</label>
              <input value={form.father_name} onChange={(e) => updateField("father_name", e.target.value)} />
            </div>
            <div>
              <label>Prezime</label>
              <input value={form.last_name} onChange={(e) => updateField("last_name", e.target.value)} />
            </div>
            <div>
              <label>JMBG</label>
              <input value={form.jmbg} onChange={(e) => updateField("jmbg", e.target.value)} maxLength={13} />
            </div>
            <div>
              <label>Radno mesto</label>
              <input value={form.job_title} onChange={(e) => updateField("job_title", e.target.value)} />
            </div>
            <div>
              <label>Email</label>
              <input type="email" value={form.email} onChange={(e) => updateField("email", e.target.value)} />
            </div>
            <div>
              <label>Lozinka</label>
              <input type="password" value={form.password} onChange={(e) => updateField("password", e.target.value)} />
            </div>
          </div>
          <button className="btn" style={{ marginTop: "16px" }} onClick={createUser}>
            Sačuvaj
          </button>
        </div>
      )}

      {/* Dodela uloge */}
      <div className="card">
        <h3 style={{ marginBottom: "16px" }}>Dodela uloge</h3>
        <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
          <div style={{ flex: 1 }}>
            <label>Korisnik</label>
            <select
              value={roleAssign.userId}
              onChange={(e) => setRoleAssign({ ...roleAssign, userId: Number(e.target.value) })}
            >
              <option value="">-- izaberi --</option>
              {users.filter((u) => u.is_active).map((u) => (
                <option key={u.id} value={u.id}>
                  {u.first_name} {u.last_name}
                </option>
              ))}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label>Uloga</label>
            <select
              value={roleAssign.roleId}
              onChange={(e) => setRoleAssign({ ...roleAssign, roleId: Number(e.target.value) })}
            >
              <option value="">-- izaberi --</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>
          <button className="btn" onClick={assignRole}>Dodeli</button>
        </div>
      </div>

      {/* Lista korisnika */}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Ime i prezime</th><th>Email</th><th>Radno mesto</th>
              <th>Status</th><th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.first_name} {u.father_name?.[0] ? u.father_name[0] + "." : ""} {u.last_name}</td>
                <td>{u.email}</td>
                <td>{u.job_title}</td>
                <td>
                  <span className={`badge ${u.is_active ? "badge-odrzan" : "badge-otkazan"}`}>
                    {u.is_active ? "Aktivan" : "Neaktivan"}
                  </span>
                </td>
                <td>
                  {u.is_active && (
                    <button className="btn btn-sm btn-danger" onClick={() => deactivateUser(u.id)}>
                      Deaktiviraj
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}