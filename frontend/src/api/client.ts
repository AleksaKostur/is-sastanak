import axios from "axios";

// tri servisa, tri base URL-a
export const authApi = axios.create({ baseURL: "http://localhost:8001" });
export const meetingApi = axios.create({ baseURL: "http://localhost:8002" });
export const reportApi = axios.create({ baseURL: "http://localhost:8003" });

// interceptor: automatski dodaje Bearer token na svaki zahtev
const attachToken = (config: any) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

authApi.interceptors.request.use(attachToken);
meetingApi.interceptors.request.use(attachToken);
reportApi.interceptors.request.use(attachToken);

// interceptor: na 401 pokušaj refresh, pa ponovi zahtev
const handle401 = (api: ReturnType<typeof axios.create>) => {
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const original = error.config;
      if (error.response?.status === 401 && !original._retry) {
        original._retry = true;
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          try {
            const { data } = await authApi.post("/auth/refresh", {
              refresh_token: refreshToken,
            });
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            original.headers.Authorization = `Bearer ${data.access_token}`;
            return api(original);
          } catch {
            localStorage.clear();
            window.location.href = "/login";
          }
        } else {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );
};

handle401(authApi);
handle401(meetingApi);
handle401(reportApi);