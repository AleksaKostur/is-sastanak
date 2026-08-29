import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout() {
  const { roles, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="logo">IS SASTANAK</div>
        <nav>
          <NavLink to="/" end>Početna</NavLink>
          <NavLink to="/meetings">Sastanci</NavLink>
          <NavLink to="/calendar">Kalendar</NavLink>
          <NavLink to="/notifications">Notifikacije</NavLink>
          {hasRole("ADMIN") && <NavLink to="/users">Korisnici</NavLink>}
        </nav>
      </aside>

      <div className="main-content">
        <header className="topbar">
          <div className="user-info">
            Uloge: {roles.length ? roles.join(", ") : "bez uloge"}
          </div>
          <button onClick={handleLogout}>Odjava</button>
        </header>
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}