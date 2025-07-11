import { createApp } from "vue";
import { createPinia } from "pinia"; // ✅ 引入 Pinia
import App from "./App.vue";
import router from "./router";
import { vuetify } from "./plugins/vuetify";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia); // ✅ 确保 Pinia 注册
app.use(router);
app.use(vuetify);
app.mount("#app");

