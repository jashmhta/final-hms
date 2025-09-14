import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import axios, { AxiosHeaders } from "axios";

axios.defaults.baseURL = "";
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  const headers = new AxiosHeaders(config.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  config.headers = headers;
  return config;
});
axios.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response && error.response.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refreshToken");
        if (!refresh) throw new Error("No refresh token");
        const r = await axios.post("/api/auth/token/refresh/", { refresh });
        const newAccess = r.data.access;
        localStorage.setItem("accessToken", newAccess);
        const h = new AxiosHeaders(original.headers);
        h.set("Authorization", `Bearer ${newAccess}`);
        original.headers = h;
        return axios(original);
      } catch {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
