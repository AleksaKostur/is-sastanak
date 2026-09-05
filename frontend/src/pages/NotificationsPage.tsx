import { useEffect, useState } from "react";
import { meetingApi } from "../api/client";
import { Pagination } from "../components/Pagination";
import type { AppNotification } from "../types";

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  const loadNotifications = () => {
    setLoading(true);
    meetingApi
      .get<AppNotification[]>("/notifications/")
      .then((res) => setNotifications(res.data))
      .catch(() => setNotifications([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const markAsRead = async (id: number) => {
    try {
      await meetingApi.patch(`/notifications/${id}/read`);
      loadNotifications();
    } catch {
      // tiho
    }
  };

  const markAllAsRead = async () => {
    try {
      await meetingApi.patch("/notifications/read-all");
      loadNotifications();
    } catch {
      // tiho
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const typeLabel: Record<string, string> = {
    USPESNO: "Uspešno",
    NEUSPESNO: "Neuspešno",
    PROMENA_OD_DRUGOG: "Promena",
  };

  const typeColor: Record<string, string> = {
    USPESNO: "#27ae60",
    NEUSPESNO: "#e74c3c",
    PROMENA_OD_DRUGOG: "#f39c12",
  };

  if (loading) return <p>Učitavanje...</p>;
  
  const sortedNotifications = [...notifications].sort((a, b) => b.id - a.id);

  const paginatedNotifications = sortedNotifications.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>
          Notifikacije {unreadCount > 0 && <span style={{ color: "#3498db" }}>({unreadCount})</span>}
        </h2>
        {unreadCount > 0 && (
          <button className="btn btn-sm" onClick={markAllAsRead}>
            Označi sve kao pročitano
          </button>
        )}
      </div>

      <div className="card">
        {notifications.length === 0 ? (
          <p style={{ color: "#7f8c8d" }}>Nemate notifikacija.</p>
        ) : (
          <div>
            {paginatedNotifications.map((n) => (
              <div
                key={n.id}
                style={{
                  padding: "16px",
                  borderBottom: "1px solid #ecf0f1",
                  background: n.is_read ? "white" : "#f0f7ff",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        color: typeColor[n.type] || "#7f8c8d",
                        textTransform: "uppercase",
                      }}
                    >
                      {typeLabel[n.type] || n.type}
                    </span>
                    {!n.is_read && (
                      <span
                        style={{
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          background: "#3498db",
                          display: "inline-block",
                        }}
                      />
                    )}
                  </div>
                  <div style={{ fontSize: "14px" }}>{n.message}</div>
                  {n.created_at && (
                    <div style={{ fontSize: "12px", color: "#95a5a6", marginTop: "4px" }}>
                      {new Date(n.created_at + "Z").toLocaleString("sr-RS")}
                    </div>
                  )}
                </div>
                {!n.is_read && (
                  <button className="btn btn-sm" onClick={() => markAsRead(n.id)}>
                    Pročitano
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
        <Pagination
          currentPage={currentPage}
          totalItems={notifications.length}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
        />
      </div>
    </>
  );
}