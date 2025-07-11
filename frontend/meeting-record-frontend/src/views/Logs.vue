<template>
  <div class="container">
    <h2>📜 操作ログ</h2>

    <div class="log-list">
      <div v-for="log in logs" :key="log.timestamp" class="log-item">
        <p>📅 {{ log.timestamp }}</p>
        <p>👤 ユーザーID: {{ log.user }}</p>
        <p>📌 {{ log.action }}: {{ log.detail }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../api";

export default {
  data() {
    return {
      logs: []
    };
  },
  methods: {
    async fetchLogs() {
      try {
        const response = await api.get("/api/logs");
        this.logs = response.data;
      } catch (error) {
        console.error("ログの取得失敗:", error);
      }
    }
  },
  mounted() {
    this.fetchLogs();
  }
};
</script>

