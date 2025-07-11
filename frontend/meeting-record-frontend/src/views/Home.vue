<template>
  <v-container class="py-6">
    <!-- ローディング -->
    <v-overlay :model-value="loading" class="align-center justify-center">
      <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
    </v-overlay>

    <v-row align="center" class="mb-4">
      <v-col class="d-flex align-center" cols="auto">
        <h2 class="text-h5 mb-0">📝 会議一覧</h2>
      </v-col>

      <v-col cols="auto" v-if="['Admin', 'Leader'].includes(userRole)">
        <v-tooltip text="新しい会議を作成">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              variant="text"
              size="small"
              color="primary"
              @click="openMeetingModal"
              class="ml-2"
            >
              <v-icon size="20">mdi-plus</v-icon>
            </v-btn>
          </template>
        </v-tooltip>
      </v-col>
    </v-row>

    <!-- ✅ 会议列表 -->
    <v-row dense class="meeting-list">
      <v-col v-for="meeting in meetings" :key="meeting.id" cols="12" sm="6" md="4">
        <v-card class="pa-4" @click="openMeeting(meeting.id)" elevation="2">
          <v-card-title class="d-flex justify-space-between align-center">
            <span class="text-h6">📅 {{ meeting.title }}</span>
            <v-chip size="small" :color="meeting.status === '開催中' ? 'green' : meeting.status === '終了' ? 'grey' : 'primary'" dark>
              {{ meeting.status }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <div>📆 {{ formatDateTime(meeting.date) }}</div>
            <div>🎤 司会者: {{ meeting.facilitator || "未定" }}</div>
            <div>📝 記録者: {{ meeting.recorder || "未定" }}</div>
            <div v-if="meeting.online_meeting_url">
              📡
              <span v-if="isValidURL(meeting.online_meeting_url)">
                <a :href="meeting.online_meeting_url" target="_blank">会議URL</a>
              </span>
              <span v-else>
                {{ meeting.online_meeting_url }}
              </span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-alert v-if="meetings.length === 0" type="info" class="mt-4">📌 まだ会議がありません。</v-alert>

    <!-- ✅ 创建会议弹窗 -->
    <v-dialog v-model="showModal" max-width="500">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h6">➕ 新しい会議を作成</span>
          <v-btn icon @click="closeMeetingModal">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-text-field v-model="newMeeting.title" label="会議タイトル" placeholder="リーダー定例会" outlined dense></v-text-field>

          <v-text-field
            v-model="newMeeting.date"
            label="会議日時"
            type="datetime-local"
            outlined
            dense
          ></v-text-field>

          <v-select
            v-model="newMeeting.facilitator"
            :items="users"
            item-value="id"
            :item-title="user => user.fullname || user.username"
            label="司会者"
            outlined
            dense
          ></v-select>

          <v-select
            v-model="newMeeting.recorder"
            :items="users"
            item-value="id"
            :item-title="user => user.fullname || user.username"
            label="議事録担当"
            outlined
            dense
          ></v-select>

          <v-text-field
            v-model="newMeeting.online_meeting_url"
            label="会議場所（Web会議URL または 会議室名）"
            placeholder="https://zoom.us/j/..."
            outlined
            dense
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-btn color="primary" block @click="createMeeting">📤 作成</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "@/store";
import { useRouter } from "vue-router";
import api from "@/api";
import axios from "axios";

const authStore = useAuthStore();
const user = computed(() => authStore.user);
const userRole = computed(() => user.value?.group || "ゲスト");
const router = useRouter();
const isLoggedIn = computed(() => !!authStore.user);
const meetings = ref([]);
const users = ref([]);
const showModal = ref(false);
const loading = ref(false);

const newMeeting = ref({
  title: "リーダー定例会",
  date: getDefaultMeetingTime(),
  facilitator: "",
  recorder: "",
  online_meeting_url: "",
});

const isValidURL = (string) => {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
};

function getDefaultMeetingTime() {
  const now = new Date();
  now.setHours(11, 0, 0, 0);
  const offset = now.getTimezoneOffset() * 60000;
  const localISOTime = new Date(now - offset).toISOString().slice(0, 16);
  return localISOTime;
}

const formatDateTime = (datetime) => {
  if (!datetime) return "未定";
  return new Date(datetime).toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

const fetchMeetings = async () => {
  loading.value = true;
  try {
    const response = await api.get("/api/meetings");
    meetings.value = response.data.sort((a, b) => new Date(b.date) - new Date(a.date));
  } catch (error) {
    console.error("会議データの取得失敗:", error);
  } finally {
    loading.value = false;
  }
};

const fetchUsers = async () => {
  loading.value = true;
  try {
    const response = await api.get("/api/users");
    users.value = response.data;
  } catch (error) {
    console.error("ユーザー取得失敗:", error);
  } finally {
    loading.value = false;
  }
};

const openMeetingModal = async () => {
  await fetchUsers();
  showModal.value = true;
};

const closeMeetingModal = () => {
  showModal.value = false;
};

const createMeeting = async () => {
  if (!newMeeting.value.title || !newMeeting.value.date || !newMeeting.value.facilitator || !newMeeting.value.recorder) {
    alert("全ての項目を入力してください！");
    return;
  }

  loading.value = true;
  try {
    await api.post("/api/meetings", {
      title: newMeeting.value.title,
      date: newMeeting.value.date,
      facilitator_id: newMeeting.value.facilitator,
      recorder_id: newMeeting.value.recorder,
      online_meeting_url: newMeeting.value.online_meeting_url || null,
    });

    closeMeetingModal();
    fetchMeetings();
  } catch (error) {
    console.error("会議の作成失敗:", error);
  } finally {
    loading.value = false;
  }
};

const openMeeting = async (id) => {
  loading.value = true;
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("ログインが必要です");
      return;
    }

    const response = await axios.get(`/api/meetings/${id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    console.log("✅ 会議データ:", response.data);
    router.push(`/meeting/${id}`);
  } catch (error) {
    console.error("❌ 会議の取得失敗:", error);
    alert("会議の取得に失敗しました");
  } finally {
    loading.value = false;
  }
};

onMounted(fetchMeetings);
</script>
