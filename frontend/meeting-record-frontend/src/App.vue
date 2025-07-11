<template>
  <v-app>
    <v-app-bar app color="primary" dark flat>
      <v-container class="d-flex justify-space-between align-center">
        <!-- Home Link -->
        <router-link class="home-link" to="/">
          <v-icon class="mr-2">mdi-home</v-icon>
          <span class="text-no-wrap">ホーム</span>
        </router-link>

        <!-- User Menu -->
        <v-menu v-model="menu" offset-y>
          <template #activator="{ props }">
            <v-btn text v-bind="props" class="d-flex align-center text-no-wrap">
              <v-icon class="mr-1">mdi-account</v-icon>
              <span class="mr-1">{{ authStore.user.fullname || authStore.user.username }}</span>
              <v-icon>mdi-menu-down</v-icon>
            </v-btn>
          </template>
          <v-list>
            <v-list-item v-if="authStore.user?.group === 'Admin'" @click="goToAdminPanel">
              <v-list-item-content class="d-flex align-center">
                <v-icon class="mr-2">mdi-cog</v-icon>
                <v-list-item-title>管理者パネル</v-list-item-title>
              </v-list-item-content>
            </v-list-item>

            <v-list-item @click="goToDelivery">
              <v-list-item-content class="d-flex align-center">
                <v-icon class="mr-2">mdi-truck-delivery</v-icon>
                <v-list-item-title>納品管理</v-list-item-title>
              </v-list-item-content>
            </v-list-item>

            <v-list-item @click="logout">
              <v-list-item-content class="d-flex align-center">
                <v-icon class="mr-2" color="red">mdi-logout</v-icon>
                <v-list-item-title class="text-red">ログアウト</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-container>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from "vue";
import { useAuthStore } from "@/store";
import { useRouter } from "vue-router";
import api from "@/api";

const authStore = useAuthStore();
const router = useRouter();
const menu = ref(false);

const logout = async () => {
  try {
    await api.post("/api/auth/logout");
  } catch (error) {
    console.error("Logout failed", error);
  }

  authStore.logout();
  router.push("/login");
};

const goToAdminPanel = () => {
  if (authStore.user?.group === "Admin") {
    router.push("/admin");
  }
};

const goToDelivery = () => {
  router.push("/deliveries");
};
</script>

<style scoped>
.text-decoration-none {
  text-decoration: none;
}
.text-red {
  color: red;
}
.text-no-wrap {
  white-space: nowrap;
}
.home-link {
  display: flex;
  align-items: center;
  color: white;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background-color 0.3s ease;
}

.home-link:hover {
  background-color: rgba(255, 255, 255, 0.2);
}
</style>
