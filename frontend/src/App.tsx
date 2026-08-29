import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
// import { MeetingsPage } from "./pages/MeetingsPage";
// import { MeetingDetailPage } from "./pages/MeetingDetailPage";
// import { CalendarPage } from "./pages/CalendarPage";
// import { UsersPage } from "./pages/UsersPage";
// import { NotificationsPage } from "./pages/NotificationsPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            {/* <Route path="meetings" element={<MeetingsPage />} />
            <Route path="meetings/:id" element={<MeetingDetailPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route
              path="users"
              element={
                <ProtectedRoute roles={["ADMIN"]}>
                  <UsersPage />
                </ProtectedRoute>
              } 
            /> */}
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}