<template>
  <div class="container">
    <h2>新規登録</h2>
    <form @submit.prevent="register">
      
      <!-- ✅ 用户名 -->
      <input v-model="username" placeholder="ユーザー名 (ログインID)" required class="input-field" />

      <!-- ✅ 姓名 -->
      <div class="name-fields">
        <input v-model="firstName" placeholder="姓" required class="input-field name-input" />
        <input v-model="lastName" placeholder="名" required class="input-field name-input" />
      </div>

      <!-- ✅ 密码 -->
      <div class="password-container">
        <input 
          :type="showPassword ? 'text' : 'password'"
          v-model="password"
          placeholder="パスワード (Password)" 
          required 
          class="input-field password-input"
        />
        <button type="button" class="toggle-password" @click="togglePassword">
          {{ showPassword ? '🙈' : '👁' }} 
        </button>
      </div>

      <!-- ✅ 确认密码 -->
      <div class="password-container">
        <input 
          :type="showPasswordConfirm ? 'text' : 'password'"
          v-model="confirmPassword"
          placeholder="パスワード確認" 
          required 
          class="input-field password-input"
        />
        <button type="button" class="toggle-password" @click="togglePasswordConfirm">
          {{ showPasswordConfirm ? '🙈' : '👁' }} 
        </button>
      </div>

      <!-- ✅ 注册按钮 -->
      <button type="submit" class="register-btn">登録</button>
    </form>

    <p>既にアカウントをお持ちですか？ <router-link to="/login">ログイン</router-link></p>
  </div>
</template>

<script>
import api from "../api";

export default {
  data() {
    return {
      username: "",
      firstName: "",  // ✅ 单独存储姓
      lastName: "",   // ✅ 单独存储名
      password: "",
      confirmPassword: "",
      showPassword: false,
      showPasswordConfirm: false
    };
  },
  methods: {
    async register() {
      if (!this.username || !this.firstName || !this.lastName || !this.password || !this.confirmPassword) {
        alert("すべての項目を入力してください！");
        return;
      }

      // ✅ 密码一致性检查
      if (this.password !== this.confirmPassword) {
        alert("パスワードが一致しません！");
        return;
      }

      // ✅ 生成完整的姓名（去掉首尾空格并合并）
      const fullName = `${this.firstName.trim()} ${this.lastName.trim()}`;

      try {
        const response = await api.post("/api/auth/register", {
          username: this.username,
          fullname: fullName,  // ✅ 发送合并后的 fullName
          password: this.password,
        });

        alert("登録成功！管理者の承認をお待ちください。");
        this.$router.push("/login");
      } catch (error) {
        console.error("登録エラー:", error);
        alert(error.response?.data?.detail || "登録に失敗しました");
      }
    },
    togglePassword() {
      this.showPassword = !this.showPassword;
    },
    togglePasswordConfirm() {
      this.showPasswordConfirm = !this.showPasswordConfirm;
    }
  },
};
</script>

<style scoped>
/* ✅ 页面样式 */
.container {
  max-width: 400px;
  margin: auto;
  padding: 20px;
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

/* ✅ 姓名输入框样式 */
.name-fields {
  display: flex;
  gap: 10px;
}

.name-input {
  flex: 1;
}

/* ✅ 密码输入框容器 */
.password-container {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input {
  width: 100%;
  padding-right: 40px; /* ✅ 预留空间给眼睛图标 */
}

.toggle-password {
  position: absolute;
  right: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
}

/* ✅ 按钮样式 */
.register-btn {
  width: 100%;
  padding: 12px;
  font-size: 18px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.register-btn:hover {
  background: #0056b3;
}
</style>
