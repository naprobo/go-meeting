<template>
  <v-container v-if="meetingDetails" class="py-4">

    <v-overlay :model-value="loading" class="d-flex justify-center align-center" persistent>
      <v-progress-circular indeterminate size="64"></v-progress-circular>
    </v-overlay>

    <!-- ✅ 会议标题区域 -->
    <v-row align="center" justify="space-between" class="mb-6">
      <v-col class="d-flex align-center gap-3" cols="12" md="8">
        <v-icon color="primary">mdi-calendar-blank</v-icon>
        <h2 class="text-h5 font-weight-medium mb-0">{{ meetingDetails.title }}</h2>

        <!-- 下载按钮 -->
        <v-tooltip
          text="全員分報告＋議事録をダウンロード"
          v-if="['Admin', 'Leader'].includes(userGroup) && meetingDetails.status === '終了'"
        >
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              variant="text"
              size="small"
              @click.stop="downloadAllReports"
            >
              <v-icon size="20">mdi-download</v-icon>
            </v-btn>
          </template>
        </v-tooltip>

        <!-- 编辑按钮 -->
        <v-tooltip
          text="会議を編集"
          v-if="['Admin', 'Leader'].includes(userGroup) && meetingDetails.status !== '終了'"
        >
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              variant="text"
              size="small"
              @click="openEditMeetingModal"
            >
              <v-icon size="20">mdi-pencil</v-icon>
            </v-btn>
          </template>
        </v-tooltip>
      </v-col>
    </v-row>

    <!-- ✅ 会議概要信息 -->
    <v-row class="mb-4" dense>
      <v-col cols="12" md="4">
        <div class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-calendar</v-icon>
          <div><strong>会議日時:</strong> {{ formatDateTime(meetingDetails.date) }}</div>
        </div>
      </v-col>

      <v-col cols="12" md="2" v-if="meetingDetails.facilitator">
        <div class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-account-voice</v-icon>
          <div><strong>司会者:</strong> {{ meetingDetails.facilitator }}</div>
        </div>
      </v-col>

      <v-col cols="12" md="2" v-if="meetingDetails.recorder">
        <div class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-pencil</v-icon>
          <div><strong>記録者:</strong> {{ meetingDetails.recorder }}</div>
        </div>
      </v-col>

      <v-col cols="12" md="2">
        <div class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-map-marker</v-icon>
          <div>
            <strong>会議場所:</strong>
            <span v-if="isValidURL(meetingDetails.online_meeting_url)">
              <a :href="meetingDetails.online_meeting_url" target="_blank">会議URL</a>
            </span>
            <span v-else>{{ meetingDetails.online_meeting_url || '未設定' }}</span>
          </div>
        </div>
      </v-col>

      <v-col cols="12" md="2">
        <div class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-flag</v-icon>
          <div>
            <strong>会議状態:</strong>
            <span :class="{
              'text-success': meetingDetails.status === '開催中',
              'text-error': meetingDetails.status === '終了',
              'text-grey': meetingDetails.status !== '開催中' && meetingDetails.status !== '終了'
            }">
              {{ meetingDetails.status }}
            </span>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- 操作按钮区域 -->
    <v-row class="my-4" dense>
      <v-col
        cols="12"
        sm="6"
        md="3"
        v-if="!loading && isFacilitator && meetingDetails.status === '未開始'"
      >
        <v-btn
          block
          color="primary"
          prepend-icon="mdi-rocket-launch"
          @click="startMeeting"
        >
          会議を開始
        </v-btn>
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="3"
        v-if="!loading && isFacilitator && meetingDetails.status === '開催中'"
      >
        <v-btn
          block
          color="error"
          prepend-icon="mdi-stop"
          @click="endMeeting"
        >
          会議を終了
        </v-btn>
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="3"
        v-if="['Leader', 'Admin'].includes(userGroup) && meetingDetails.status !== '終了'"
      >
        <v-btn
          block
          color="secondary"
          prepend-icon="mdi-file-document-edit"
          @click="goToSubmitReport"
        >
          {{ hasUserReport ? `${userFullName}の進捗報告を編集` : `${userFullName}の進捗報告を提出` }}
        </v-btn>
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="3"
        v-if="isRecorder"
      >
        <v-btn
          block
          color="success"
          prepend-icon="mdi-notebook-edit"
          @click="showMinutesEditModal"
        >
          {{ hasMinutes ? '議事録を編集' : '議事録を作成' }}
        </v-btn>
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="3"
        v-if="['Admin', 'Leader'].includes(userGroup) && meetingDetails.status === '終了'"
      >
        <v-btn
          block
          color="info"
          prepend-icon="mdi-notebook-outline"
          @click="showMinutesViewModal"
        >
          会議の議事録を閲覧
        </v-btn>
      </v-col>

      <v-col cols="12" v-if="meetingDetails.status === '終了'">
        <v-alert
          type="warning"
          border="start"
          color="deep-orange-darken-2"
          icon="mdi-alert-circle"
          prominent
          density="comfortable"
          class="mt-2"
        >
          この会議は <strong>終了</strong> しています。<br />
          <span class="text-body-2">進捗報告の編集・提出はできません。</span>
        </v-alert>
      </v-col>
    </v-row>

    <!-- ✅ 会议编辑弹窗 -->
    <v-dialog v-model="showEditModal" max-width="600px" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h6">✏️ 会議を編集</span>
          <v-btn icon @click="closeEditMeetingModal">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text class="pt-4">
          <v-text-field
            label="会議タイトル"
            v-model="editMeeting.title"
            density="comfortable"
            variant="outlined"
          />

          <v-text-field
            label="会議日時"
            v-model="editMeeting.date"
            type="datetime-local"
            density="comfortable"
            variant="outlined"
          />

          <v-select
            label="司会者"
            v-model="editMeeting.facilitator_id"
            :items="userOptions"
            item-value="id"
            item-title="name"
            density="comfortable"
            variant="outlined"
          />

          <v-select
            label="議事録担当"
            v-model="editMeeting.recorder_id"
            :items="userOptions"
            item-value="id"
            item-title="name"
            density="comfortable"
            variant="outlined"
          />

          <v-text-field
            label="会議場所（Web会議URL または 会議室名）"
            v-model="editMeeting.online_meeting_url"
            density="comfortable"
            variant="outlined"
          />
        </v-card-text>

        <v-divider class="my-2"></v-divider>

        <v-card-actions class="justify-end px-4 pb-4">
          <v-btn color="primary" @click="updateMeeting">
            💾 保存
          </v-btn>
          <v-btn @click="closeEditMeetingModal" variant="text">キャンセル</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ✅ 進捗報告一覧 -->
    <v-row class="mt-8">
      <v-col cols="12">
        <h3 class="text-h5 font-weight-medium mb-4 text-left">進捗報告一覧</h3>
        <v-row dense>
          <v-col
            v-for="report in reports"
            :key="report.id"
            cols="12"
            class="mb-2"
          >
          <v-btn
            block
            :disabled="loadingReportId === report.id"
            :color="clickedReports.has(report.id) ? 'grey-darken-2' : 'primary'"
            variant="elevated"
            class="text-left justify-start py-4 px-3"
            @click="showReport(report)"
          >
            <template #prepend>
              <v-icon>
                {{ clickedReports.has(report.id) ? 'mdi-email-open' : 'mdi-email' }}
              </v-icon>
            </template>

            <div class="d-flex align-center">
              <span class="text-subtitle-1 font-weight-medium">
                {{ report.user.fullname || report.user.username }}
              </span>
              <v-progress-circular
                v-if="loadingReportId === report.id"
                indeterminate
                color="white"
                size="18"
                width="2"
                class="ml-2"
              />
            </div>
          </v-btn>
          </v-col>
        </v-row>
        <p v-if="reports.length === 0" class="text-grey">📌 まだ報告がありません。</p>
      </v-col>
    </v-row>

    <!-- ✅ 报告详情弹窗 -->
    <v-dialog v-model="showReportModal" fullscreen scrollable>
      <v-card class="d-flex flex-column" style="height: 100vh">
        <v-card-text class="pa-0 d-flex flex-column" style="height: 100vh;">
          <v-sheet
            class="flex-grow-1 bg-grey-lighten-4 overflow-auto pa-4"
            rounded
          >
            <ul v-if="selectedReport && selectedReport.reports">
              <li v-for="report in selectedReport.reports" :key="report.id">
                <div v-for="(project, projectIndex) in report.projects" :key="projectIndex" class="mb-6">
                  <hr class="thick-hr" />
                  <div v-if="project.fields.length > 0">
                    <div v-for="(field, fieldIndex) in project.fields" :key="fieldIndex" class="mb-4">
                      <p class="field-title-large">{{ field.title }}</p>
                      <div
                        v-if="isComparisonMode && previousReport"
                        v-html="highlightDiffBlock(field.value || '', getPreviousFieldValue(projectIndex, field.title))"
                        class="pl-4"
                      />
                      <div
                        v-else
                        v-html="highlightText(field.value || '')"
                        class="pl-4"
                      />
                    </div>
                  </div>
                  <p v-else class="text-grey">⚠️ このプロジェクトには報告内容がありません。</p>
                </div>
              </li>
            </ul>
          </v-sheet>

          <!-- ✅ 浮动按钮 -->
          <div class="floating-button-group">
            <v-btn color="info" @click="toggleComparison">
              {{ isComparisonMode ? '非比較' : '比較' }}
            </v-btn>
            <v-btn color="error" @click="closeModal">閉じる</v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>


    <!-- ✅ 議事録閲覧モーダル -->
    <v-dialog v-model="showMinutesView" fullscreen scrollable>
      <v-card class="d-flex flex-column" style="height: 100vh">
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h6">📜 議事録</span>
          <v-progress-circular
            v-if="loadingMinutes"
            indeterminate
            color="primary"
            size="20"
          ></v-progress-circular>
        </v-card-title>

        <v-card-text class="px-6 flex-grow-1">
          <v-divider class="my-4"></v-divider>

          <v-sheet class="pa-4 bg-grey-lighten-4 overflow-auto" rounded style="max-height: calc(100vh - 200px)">
            <div class="mb-6">
              <p class="text-subtitle-1 font-weight-bold mb-1">■日時</p>
              <pre class="minutes-pre">{{ formatDisplayDate(minutesData.content.date) }}</pre>
            </div>

            <div class="mb-6">
              <p class="text-subtitle-1 font-weight-bold mb-1">■議題</p>
              <pre class="minutes-pre">{{ minutesData.content.topics || '未入力' }}</pre>
            </div>

            <div class="mb-6">
              <p class="text-subtitle-1 font-weight-bold mb-1">■各案件の報告担当</p>
              <pre class="minutes-pre">{{ minutesData.content.responsibilities || '未入力' }}</pre>
            </div>

            <div>
              <p class="text-subtitle-1 font-weight-bold mb-1">■議事録</p>
              <pre class="minutes-pre">{{ minutesData.content.details || '未入力' }}</pre>
            </div>

          </v-sheet>
        </v-card-text>

        <v-card-actions class="justify-end px-6 pb-4">
          <v-btn color="primary" @click="closeMinutesViewModal">閉じる</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ✅ 議事録編集モーダル（フルスクリーン化） -->
    <v-dialog v-model="showMinutesEdit" fullscreen scrollable>
      <v-card class="d-flex flex-column" style="height: 100vh">
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h6">📜 議事録 {{ isNewMinutes ? '作成' : '編集' }}</span>
          <v-progress-circular
            v-if="loadingMinutes"
            indeterminate
            color="primary"
            size="20"
          ></v-progress-circular>
        </v-card-title>

        <v-card-text class="px-6 flex-grow-1">
          <v-divider class="my-4"></v-divider>

          <v-container fluid class="overflow-auto" style="max-height: calc(100vh - 200px)">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="minutesData.content.date"
                  label="■日時"
                  type="datetime-local"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="minutesData.content.topics"
                  label="■議題"
                  auto-grow
                  rows="1"
                  placeholder="議題を入力..."
                ></v-textarea>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="minutesData.content.responsibilities"
                  label="■各案件の報告担当"
                  auto-grow
                  rows="1"
                  placeholder="案件の担当者を記入..."
                ></v-textarea>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="minutesData.content.details"
                  label="■議事録"
                  auto-grow
                  rows="10"
                  placeholder="議事録の内容を記入..."
                ></v-textarea>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>

        <v-card-actions class="justify-end px-6 pb-4">
          <v-btn color="primary" @mousedown="saveMinutes">
            📤 {{ isNewMinutes ? '議事録を提出' : '議事録を更新' }}
          </v-btn>
          <v-btn @click="closeMinutesEditModal">閉じる</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useAuthStore } from "@/store";
import { useRouter, useRoute } from "vue-router";
import DiffMatchPatch from "diff-match-patch";
import JSZip from "jszip";
import { saveAs } from "file-saver";
import api from "@/api";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const loading = ref(false);

const userGroup = computed(() => authStore.user?.group || "Guest");
const userId = computed(() => authStore.user?.id);
const userFullName = computed(() => authStore.user?.fullname || authStore.user?.username || "あなた");
const meetingId = ref(route.params.meetingId);
const meetingDetails = ref(null);
const reports = ref([]);
const selectedReport = ref(null);
const loadingReport = ref(false);
const loadingMinutes = ref(false);
const showMinutes = ref(false);

const users = ref([]);
const showEditModal = ref(false);
const showReportModal = ref(false);

const editMeeting = ref({
  title: "",
  date: "",
  facilitator: "",
  recorder: "",
  online_meeting_url: "",
});

const showMinutesView = ref(false);  // ✅ 控制【阅览模式】弹窗
const showMinutesEdit = ref(false);  // ✅ 控制【编辑模式】弹窗

const loadingReportId = ref(null);

const userOptions = computed(() =>
  users.value.map(user => ({
    id: user.id,
    name: user.fullname || user.username || '（不明）'
  }))
);

// ✅ 是否有议事录数据
const hasMinutes = computed(() => {
  return minutesData.value && minutesData.value.content &&
         Object.keys(minutesData.value.content.details).length > 0;
});

// ✅ 是否是会议记录者
const isRecorder = computed(() => meetingDetails.value?.recorder_id === userId.value);

// ✅ 会议是否已结束
const isMeetingEnded = computed(() => meetingDetails.value?.status === '終了');

// ✅ 只有【会议记录者】能编辑议事录
const showMinutesEditModal = () => {
  if (!isRecorder.value) return;
  showMinutesEdit.value = true;
  fetchMinutes();
};

// ✅ 会议结束后，只有【Admin & Leader】能阅览
const showMinutesViewModal = () => {
  if (!isMeetingEnded.value) return;
  showMinutesView.value = true;
  fetchMinutes();
};

// ✅ 关闭阅览模式
const closeMinutesViewModal = () => {
  showMinutesView.value = false;
};

// ✅ 关闭编辑模式
const closeMinutesEditModal = () => {
  showMinutesEdit.value = false;
};

// ✅ 自动展开 & 收缩输入框
const expandTextarea = (event) => {
  event.target.rows = 16;
};

const shrinkTextarea = (event) => {
  event.target.rows = 1;
};

// ✅ 获取用户列表
const fetchUsers = async () => {
  try {
    const response = await api.get("/api/users");
    users.value = response.data;
  } catch (error) {
    console.error("ユーザー取得失敗:", error);
  }
};

// ✅ 打开会议编辑弹窗
const openEditMeetingModal = async () => {
  await fetchUsers();
  editMeeting.value = { ...meetingDetails.value }; // 复制当前会议数据
  showEditModal.value = true;
};

// ✅ 关闭会议编辑弹窗
const closeEditMeetingModal = () => {
  showEditModal.value = false;
};

// ✅ 更新会议信息
const updateMeeting = async () => {
  try {
    await api.put(`/api/meetings/${meetingId.value}`, editMeeting.value);
    showEditModal.value = false;
    fetchMeetingDetails();
    // alert("会議が更新されました！");
  } catch (error) {
    console.error("会議の更新失敗:", error);
  }
};

// ✅ 是否有当前用户的报告
const hasUserReport = computed(() => reports.value.some(report => report.user_id === userId.value));

const isFacilitator = ref(false);

watch(meetingDetails, (newVal) => {
  if (newVal) {
    isFacilitator.value = newVal.facilitator_id === userId.value;
  }
});

const startMeeting = async () => {
  try {
    const response = await api.post(`/api/meetings/${meetingId.value}/start`);
    meetingDetails.value.status = response.data.status; // ✅ 更新状态
    // alert("会議を開始しました！");
  } catch (error) {
    console.error("会議の開始に失敗:", error);
    alert(error.response?.data?.detail || "会議の開始に失敗しました");
  }
};

const endMeeting = async () => {
  // 🚨 显示警告弹窗
  const userConfirmed = confirm(
    "⚠️ この会議を終了してもよろしいですか？\n\n終了後は、進捗報告の編集ができなくなります。\n（※議事録の編集は可能です）"
  );

  if (!userConfirmed) {
    return; // ❌ 用户取消，则不执行后续代码
  }

  try {
    const response = await api.post(`/api/meetings/${meetingId.value}/end`);
    meetingDetails.value.status = response.data.status; // ✅ 更新状态
    // alert("会議を終了しました！");
  } catch (error) {
    console.error("会議の終了に失敗:", error);
    alert(error.response?.data?.detail || "会議の終了に失敗しました");
  }
};

// ✅ 格式化日期
const formatDateTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString("ja-JP", { dateStyle: "full", timeStyle: "short" });
};

const isValidURL = (string) => {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
};

// 获取会议详情
const fetchMeetingDetails = async () => {
  loading.value = true;
  try {
    const response = await api.get(`/api/meetings/${meetingId.value}`);
    meetingDetails.value = response.data;
    // console.log("会議の詳細:", response.data);
  } catch (error) {
    console.error("会議の詳細取得失敗:", error);
  } finally {
    loading.value = false;
  }
};

const getLocalISODateTime = (dateString = null) => {
  let now = dateString ? new Date(dateString) : new Date(); // 如果有日期就用，否则用当前时间
  let offset = now.getTimezoneOffset() * 60000; // 获取时区偏移量（毫秒）
  let localTime = new Date(now - offset).toISOString().slice(0, 16); // 调整时区并去掉秒
  return localTime;
};

const minutesData = ref({
  content: {
    date: meetingDetails.value?.date ? getLocalISODateTime(meetingDetails.value.date) : getLocalISODateTime(),
    topics: "1. 全体連絡\n2. 進捗報告\n3. その他共有事項等",
    responsibilities: "",
    details: ""
  },
  is_approved: true,
});

const isNewMinutes = ref(true)

// ✅ 获取会议记录
const fetchMinutes = async () => {
  loading.value = true;
  try {
    loadingMinutes.value = true;
    const response = await api.get(`/api/meetings/${meetingId.value}/minutes`);

    if (response.data && response.data.content) {
      let parsedContent = {};
      try {
        parsedContent = JSON.parse(response.data.content);
      } catch (error) {
        console.error("❌ 議事録の JSON 解析失敗:", error);
      }

      minutesData.value = {
        ...response.data,
        content: {
          ...minutesData.value.content,
          ...parsedContent
        }
      };
      isNewMinutes.value = false;
    }

    // console.log("📜 取得した議事録:", minutesData.value);
  } catch (error) {
    if (error.response?.status === 404) {
      console.warn("📜 議事録が存在しません。新規作成モードに入ります。");
      minutesData.value = {
        content: {
          date: meetingDetails.value?.date ? getLocalISODateTime(meetingDetails.value.date) : getLocalISODateTime(),
          topics: "1. 全体連絡\n2. 進捗報告\n3. その他共有事項等",
          responsibilities: "",
          details: ""
        },
        is_approved: false,
      };
      isNewMinutes.value = true;
    } else {
      console.error("📜 議事録の取得失敗:", error);
    }
  } finally {
    loading.value = false;
    loadingMinutes.value = false;
  }
};

// ✅ 提交/更新会议记录
const saveMinutes = async () => {
  loading.value = true;
  try {
    await api.post(`/api/meetings/${meetingId.value}/minutes`, minutesData.value);
    showMinutesEdit.value = false;
    fetchMinutes();
  } catch (error) {
    console.error("議事録の保存失敗:", error);
  } finally {
    loading.value = false;
  }
};

const isEditable = ref(false);
// ✅ 显示会议记录弹窗（可编辑/只读）
const showMinutesModal = (editable) => {
  isEditable.value = editable;
  showMinutes.value = true;
  fetchMinutes();
};

// ✅ 关闭会议记录弹窗
const closeMinutesModal = () => {
  showMinutes.value = false;
};

// 获取会议报告
const fetchReports = async () => {
  loading.value = true;
  try {
    const response = await api.get(`/api/meetings/${meetingId.value}/reports`);
    reports.value = response.data.map(report => ({
      id: report.id,
      user_id: report.user_id,
      user: {
        fullname: report.user.fullname,
        username: report.user.username
      },
      content: parseContent(report.content)
    }));
    // console.log("進捗報告:", reports.value);
  } catch (error) {
    console.error("報告の取得失敗:", error);
  } finally {
    loading.value = false;
  }
};

// ✅ 解析 JSON 并处理异常
const parseContent = (content) => {
  if (!content) return [];

  try {
    const parsed = typeof content === "string" ? JSON.parse(content) : content;

    // ✅ 确保数据格式正确
    if (!Array.isArray(parsed)) {
      console.error("❌ JSON 格式错误，期望数组:", parsed);
      return [];
    }

    return parsed.map(project => ({
      fields: project.fields || [] // 兼容可能缺失 `fields`
    }));
  } catch (e) {
    console.error("❌ JSON 解析失败:", content);
    return [];
  }
};

const enterFullscreen = async () => {
  const el = document.documentElement; // 或者 document.querySelector('.v-dialog')
  if (el.requestFullscreen) {
    await el.requestFullscreen();
  }
};

const isScrolling = ref(true); // 控制滚动状态
const scrollInterval = ref(null); // 存储定时器 ID
const clickedReports = ref(new Set());
// ✅ 点击人名时，向后端获取该用户的最新报告
const showReport = async (report) => {
  if (!report.user_id) {
    console.error("❌ report.user_id 不存在", report);
    alert("報告のユーザーが無効です！");
    return;
  }

  if (loadingReportId.value === report.id) return; // 防止重复点击

  loadingReportId.value = report.id;
  loadingReport.value = true;
  selectedReport.value = null;

  try {
    const response = await api.get(`/api/meetings/${meetingId.value}/reports/user/${report.user_id}`);

    if (!response.data || !Array.isArray(response.data.reports)) {
      throw new Error("報告データが不正です");
    }

    selectedReport.value = {
      user_id: report.user_id, 
      user: response.data.user || { fullname: "Unknown", username: "Unknown" },
      reports: response.data.reports.map(r => ({
        id: r.id,
        projects: parseContent(r.content)
      }))
    };

    await fetchPreviousReport(report.user_id);
    // await new Promise(resolve => setTimeout(resolve, 5000));
    clickedReports.value.add(report.id);
    showReportModal.value = true;
    await nextTick();
    await enterFullscreen();
  } catch (error) {
    console.error("報告の取得失敗:", error.response || error);
    if (!selectedReport.value) {
      alert("報告の取得に失敗しました");
    }
  } finally {
    loadingReport.value = false;
    loadingReportId.value = null;
  }
};

const formatDisplayDate = (isoString) => {
  if (!isoString) return "未設定";
  
  const date = new Date(isoString);
  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false, // 24小时制
  }).format(date);
};

const exitFullscreen = async () => {
  if (document.fullscreenElement) {
    await document.exitFullscreen();
  }
};

// ✅ 关闭弹窗
const closeModal = () => {
  selectedReport.value = null;
  loadingReport.value = false; // ✅ 确保 loading 状态也重置
  showReportModal.value = false;
  exitFullscreen();
};

// ✅ 提交进度报告时检查会议状态
const goToSubmitReport = () => {
  if (isMeetingEnded.value) {
    alert("この会議は既に終了しています。編集できません。");
    return;
  }
  router.push(`/meeting/${meetingId.value}/newreport`);
};

// 监听 `meetingId` 变化并获取数据
watch(
  () => route.params.meetingId,
  (newId) => {
    if (newId) {
      meetingId.value = newId;
      fetchMeetingDetails();
      fetchReports();
      fetchMinutes();
    } else {
      console.error("❌ meetingId 不存在");
    }
  },
  { immediate: true }
);

const highlightText = (text) => {
  if (!text) return "未入力";

  const lines = text
    .split("\n")
    .map((line) => {
      return line.startsWith("★")
        ? `<span class="highlight-line">${line}</span><br>`
        : `<span>${line}</span><br>`;
    });

  return `<div class="report-view">${lines.join("")}</div>`;
};

const highlightDiffBlock = (current, previous) => {
  const dmp = new DiffMatchPatch();
  const diffs = dmp.diff_main(previous || "", current || "");
  dmp.diff_cleanupSemantic(diffs);

  const html = diffs.map(([op, text]) => {
    const escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    if (op === 1) return `<ins>${escaped}</ins>`;
    if (op === -1) return `<del>${escaped}</del>`;
    return `<span>${escaped}</span>`;
  }).join('');

  return `<div class="dmp-block">${html}</div>`;
};


const getPreviousFieldValue = (projectIndex, fieldTitle) => {
  // console.log("👀 previousReport.value:", previousReport.value);
  const prevProj = previousReport.value?.projects?.[projectIndex];
  if (!prevProj) return "";
  const matchedField = prevProj.fields?.find(f => f.title.trim() === fieldTitle.trim());
  return matchedField?.value || "";
};

const previousReport = ref(null);
const loadingPrevious = ref(false);
const fetchPreviousReport = async (userId) => {
  if (!meetingId.value || !userId) return;

  loadingPrevious.value = true;

  try {
    const response = await api.get(
      `/api/reports/previous/${meetingId.value}/${userId}`
    );

    const reportData = response.data.report; // ✅ 取出正确字段

    if (reportData && reportData.content) {
      previousReport.value = {
        id: reportData.id,
        projects: parseContent(reportData.content),
      };
    } else {
      console.warn("⚠️ 前回報告データが存在しません");
      previousReport.value = null;
    }

  } catch (error) {
    console.error("前回報告の取得失敗:", error);
  } finally {
    loadingPrevious.value = false;
  }
};

const isComparisonMode = ref(false);
const toggleComparison = () => {
  if (!isComparisonMode.value) {
    isComparisonMode.value = true;
  } else {
    isComparisonMode.value = false;
  }
};

const isFullscreen = ref(false);

const formatReportText = (projects) => {
  if (!Array.isArray(projects)) return "";

  return projects.map(project => {
    const fields = project.fields || [];
    if (fields.length === 0) return "";

    const firstField = fields[0];
    let result = "";

    if (firstField.title.trim() === "プロジェクト") {
      result += `◆${(firstField.value || "").trim()}\n`;
      for (let i = 1; i < fields.length; i++) {
        const f = fields[i];
        result += `　▽${(f.title || "").trim()}\n`;
        result += (f.value || "")
          .split("\n")
          .map(line => `　　${line}`)
          .join("\n") + "\n";
      }
    } else {
      result += `◆${(firstField.title || "").trim()}\n`;
      result += (firstField.value || "")
        .split("\n")
        .map(line => `　${line}`)
        .join("\n") + "\n";
    }

    return result;
  }).join("\n");
};

const formatMinutesText = (content) => {
  const { date, topics, responsibilities, details } = content || {};

  const formatBlock = (label, value, indent = "　") => {
    return `◆${label}\n` + (value || "未入力")
      .split("\n")
      .map(line => indent + line)
      .join("\n");
  };

  return [
    formatBlock("日時", formatDisplayDate(date)),
    formatBlock("議題", topics),
    formatBlock("各案件の報告担当", responsibilities),
    formatBlock("議事録", details)
  ].join("\n\n");
};

// 触发下载 zip
const downloadAllReports = async () => {
  const zip = new JSZip();
  const datePrefix = new Date(meetingDetails.value.date).toISOString().slice(0, 10).replace(/-/g, "");

  // ✅ 加入每个用户的进度报告
  for (const report of reports.value) {
    const name = report.user.fullname || report.user.username || "unknown";
    const text = formatReportText(report.content);
    zip.file(`${datePrefix}_${name}.txt`, text);
  }

  // ✅ 加入議事録（只要有就加）
  if (minutesData.value && minutesData.value.content) {
    const text = formatMinutesText(minutesData.value.content);
    zip.file(`${datePrefix}_議事録.txt`, text);
  }

  // ✅ 打包下载
  const blob = await zip.generateAsync({ type: "blob" });
  saveAs(blob, `${datePrefix}_会議資料.zip`);
};

</script>

<style scoped>
.field-title {
  font-weight: bold;
  font-size: 16px;
  margin-top: 10px;
}

.field-value {
  white-space: pre-wrap;
  word-wrap: break-word;
  padding-left: 20px;
  font-size: 15px;
  color: #333;
}

.thick-hr {
  height: 5px;
  border: none;
  background: linear-gradient(to right, #ff6b6b, #6b6bff);
  margin: 25px -10px;
}

.loading-text {
  font-size: 14px;
  color: #888;
}

::v-deep(.highlight-line) {
  font-size: 1.5rem;
  line-height: 2;
  font-weight: 500;
  background-color: yellow;
  padding: 2px 5px;
  border-radius: 3px;
  font-weight: bold;
  display: block;
}

::v-deep(.removed-line) {
  background-color: #ccc;
  padding: 2px 5px;
  border-radius: 3px;
  display: block;
}

::v-deep(.diff-line) {
  display: block;
  margin-bottom: 4px;
  white-space: pre-wrap;
}

::v-deep(.dmp-line) {
  display: block;
  white-space: pre-wrap;
  margin-bottom: 4px;
}

::v-deep(.dmp-line.modified) {
  display: block;
}

::v-deep(ins) {
  background: #e6ffe6;
  text-decoration: none;
}

::v-deep(del) {
  background: #ffe6e6;
  text-decoration: line-through;
}

::v-deep(.dmp-block) {
  font-size: 1.5rem;
  line-height: 2;
  font-weight: 500;
  font-family: Roboto, sans-serif;
  word-break: break-word;
  white-space: pre-wrap;
}

::v-deep(.dmp-block ins) {
  background: #e6ffe6;
  text-decoration: none;
}

::v-deep(.dmp-block del) {
  background: #ffe6e6;
  text-decoration: line-through;
}

::v-deep(.dmp-block span),
::v-deep(.report-view span) {
  display: inline;
  white-space: pre-wrap;
  font-size: 1.5rem;
  line-height: 2;
  font-weight: 500;
}

.field-title-large {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.floating-button-group {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  gap: 20px;
}

.floating-button-group > .v-btn {
  min-width: 120px;
  justify-content: center;
}

::v-deep(li::marker) {
  content: none;
}

.minutes-pre {
  white-space: pre-wrap;
  font-size: 1rem;
  line-height: 1.6;
  font-family: inherit;
  margin: 0;
  color: #333;
}

</style>