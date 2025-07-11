<template>
  <div class="container">
    <h2>ログイン</h2>

    <form @submit.prevent="login">
      <input v-model="username" placeholder="ユーザー名" required class="input-field" />
      <input 
        type="password"
        v-model="password"
        placeholder="パスワード" 
        required 
        class="input-field"
      />
      <button type="submit" :disabled="loading">
        {{ loading ? "ログイン中..." : "ログイン" }}
      </button>
    </form>

    <p>アカウントをお持ちでない方は <router-link to="/register">新規登録</router-link> してください。</p>

    <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useAuthStore } from "@/store";  // ✅ 使用 Pinia 管理用户状态
import { useRouter } from "vue-router";
import api from "@/api";

const authStore = useAuthStore();
const router = useRouter();

const username = ref("");
const password = ref("");
const errorMessage = ref("");
const loading = ref(false);

const login = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = "ユーザー名とパスワードを入力してください。";
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await api.post("/api/auth/login", {
      username: username.value,
      password: password.value,
    });

    authStore.setUser(response.data.user, response.data.token); // ✅ 登录后更新 Pinia 用户状态

    router.push("/");  // ✅ 登录后跳转到首页
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || "ログインに失敗しました";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* ✅ 页面样式 */
.container {
  max-width: 400px;
  margin: 50px auto;
  text-align: center;
}

/* ✅ 输入框样式 */
.input-field {
  width: 100%;
  padding: 10px;
  margin: 8px 0;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-sizing: border-box; /* ✅ 避免 padding 影响宽度 */
}

/* ✅ 按钮样式 */
button {
  width: 100%;
  padding: 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #0056b3;
}

/* ✅ 错误消息样式 */
.error-msg {
  color: red;
  margin-top: 10px;
  font-size: 14px;
}
</style>
