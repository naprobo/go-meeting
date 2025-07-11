import { defineStore } from "pinia";
import api from "./api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: JSON.parse(localStorage.getItem("user") || "null"),
    token: localStorage.getItem("token") || null,
  }),
  actions: {
    async fetchUser(meetingId = null) {
      try {
        let url = "/api/auth/me";
        if (meetingId) {
          url += `?meeting_id=${meetingId}`;
        }
        const response = await api.get(url);
        this.user = response.data;
        localStorage.setItem("group", response.data.group);
        if (meetingId) {
          localStorage.setItem(`role_meeting_${meetingId}`, response.data.role);
        }
      } catch (error) {
        console.error("ユーザー情報取得失敗:", error);
      }
    },
    setUser(user: any, token: string) {  // ✅ 显式声明参数类型
      this.user = user;
      this.token = token;
      localStorage.setItem("user", JSON.stringify(user)); // ✅ 存储用户信息
      localStorage.setItem("token", token);
    },
    logout() {
      this.user = null;
      this.token = null;
      localStorage.removeItem("user"); // ✅ 清除数据
      localStorage.removeItem("token");
    },
  },
});

