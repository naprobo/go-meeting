import { createRouter, createWebHashHistory } from "vue-router";
import Register from "../views/Register.vue";
import Login from "../views/Login.vue";
import Home from "../views/Home.vue";
import Admin from "../views/AdminPanel.vue";
import MeetingDetail from "../views/MeetingDetail.vue";
import { useAuthStore } from "../store";
import SubmitReport from "@/views/SubmitReport.vue";
import DeliveryList from "@/views/DeliveryList.vue";

const routes = [
  { path: "/", component: Home, meta: { requiresAuth: true } }, // Requires login
  { path: "/register", component: Register },
  { path: "/login", component: Login },
  { path: "/meeting/:meetingId", component: MeetingDetail, props: true, meta: { requiresAuth: true } }, // Meeting detail page
  { path: "/meeting/:meetingId/newreport", component: SubmitReport, props: true, meta: { requiresAuth: true } }, // Report submission page
  { path: "/admin", component: Admin, meta: { requiresAuth: true } }, // Admin panel
  { path: "/deliveries", component: DeliveryList, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

// Global navigation guard (redirect unauthenticated users to login page)
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.user !== null; // Check if user is logged in

  if (to.meta.requiresAuth && !isAuthenticated) {
    next("/login"); // Redirect unauthenticated users to login page
  } else {
    next();
  }
});

export default router;
