import axios from "axios";
import { useAuthStore } from "@/store";
import router from "@/router";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // 读取 .env 中的 API 地址
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// ✅ 请求拦截器：自动附加 Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ✅ 响应拦截器：处理未授权（401）错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore();
      authStore.logout(); // ✅ 清除用户信息
      router.push("/login"); // ✅ 直接跳转到登录页面
    }
    return Promise.reject(error);
  }
);

export default api;
