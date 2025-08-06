<template>
  <v-snackbar v-model="snackbar" :timeout="3000" color="success">
    {{ snackbarText }}
  </v-snackbar>

  <v-container class="py-4" style="max-width: 900px">
    <h2 class="text-h5 font-weight-bold mb-4">
      📄 {{ isEditing ? "進捗報告を編集" : "進捗報告を提出" }}
    </h2>

    <!-- ✅ 前回履歴読み込み + 比較モード設定 -->
    <v-row class="mb-4" align="center">
      <v-col cols="auto">
        <v-btn
          v-if="showLastReportReadBtn"
          @click="loadLastReport"
          prepend-icon="mdi-history"
          color="warning"
        >
          前回の履歴から読み込む
        </v-btn>
      </v-col>
      <v-col cols="auto">
        <v-checkbox
          v-model="reportData.settings.useCompareMode"
          label="会議時に比較モードで閲覧する"
          density="compact"
          hide-details
        ></v-checkbox>
      </v-col>
    </v-row>

    <!-- ✅ 複数プロジェクト -->
    <v-card
      v-for="(project, projectIndex) in reportData.projects"
      :key="projectIndex"
      class="mb-6"
      variant="outlined"
    >
      <v-card-text>
        <v-row
          v-for="(field, fieldIndex) in project.fields"
          :key="fieldIndex"
          class="mb-4"
        >
          <v-col cols="12">
            <v-textarea
              v-model="field.value"
              :label="field.title"
              auto-grow
              variant="outlined"
              rows="2"
              @focus="expandTextarea"
              @blur="shrinkTextarea"
              ref="textareas"
              hide-details
            ></v-textarea>
          </v-col>
          <v-col cols="12" class="text-end">
            <v-btn
              color="error"
              size="small"
              @click="removeField(projectIndex, fieldIndex)"
              prepend-icon="mdi-delete"
            >
              カテゴリ削除
            </v-btn>
          </v-col>
        </v-row>

        <!-- ✅ カテゴリ追加 -->
        <v-btn
          color="amber-darken-2"
          variant="tonal"
          class="me-2"
          size="small"
          @click="addNewField(projectIndex)"
          prepend-icon="mdi-plus"
        >
          カテゴリを追加
        </v-btn>

        <v-btn
          v-if="reportData.length > 1"
          color="red-darken-2"
          variant="tonal"
          size="small"
          @click="removeProject(projectIndex)"
          prepend-icon="mdi-delete"
        >
          プロジェクト削除
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- ✅ プロジェクト追加 -->
    <v-btn
      color="green"
      class="mb-4"
      @click="addNewProject"
      prepend-icon="mdi-plus-box"
    >
      新しいプロジェクトを追加
    </v-btn>

    <!-- ✅ 提出 / 閉じる -->
    <v-btn
      color="primary"
      class="mb-2"
      @click="submitReport"
      block
      prepend-icon="mdi-check"
    >
      {{ isEditing ? "更新" : "提出" }}
    </v-btn>
    <v-btn
      color="grey"
      variant="tonal"
      @click="closeAndReturn"
      block
      prepend-icon="mdi-close"
    >
      閉じる
    </v-btn>
  </v-container>
</template>

<script setup>
import { ref, onMounted, watchEffect  } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/api";
import { useAuthStore } from "@/store";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const meeting_id = route.params.meetingId;  
const user_id = authStore.user?.id;  

const isEditing = ref(false);
const reportId = ref(null);
const showLastReportReadBtn = ref(false);

const snackbar = ref(false);
const snackbarText = ref("");
const snackbarColor = ref("success"); // 可为 "error", "warning", "info" 等

const textareas = ref([]); // 存储所有的 textarea 引用

// ✅ 点击时扩大
const expandTextarea = (event) => {
  event.target.rows = 6; // 变高
};

// ✅ 失去焦点时缩小
const shrinkTextarea = (event) => {
  event.target.rows = 2; // 变回原高度
};

// ✅ 预定义的默认分类（确保每个项目都有）
const defaultFields = [
  { title: "プロジェクト", value: "" },
  { title: "工数", value: "" },
  { title: "問題点の報告", value: "" },
  { title: "案件名・技術情報", value: "" },
  { title: "客先の体制変更、客先の情報", value: "" },
  { title: "その他", value: "" }
];

// ✅ 先初始化 reportData，确保打开页面时有默认分类
const reportData = ref({
  settings: {
    useCompareMode: false, // ✅ 会議時に比較モードを使用する
  },
  projects: [
    {
      fields: JSON.parse(JSON.stringify(defaultFields))
    }
  ]
});

// ✅ 获取当前用户的会议报告（用于编辑）
const fetchExistingReport = async () => {
  try {
    const response = await api.get(`/api/meetings/${meeting_id}/reports/user/${user_id}`);
    // console.log("🎯 服务器返回的报告数据:", response.data);

    if (response.data && response.data.reports.length > 0) {
      const reportContent = JSON.parse(response.data.reports[0].content);
      // console.log("✅ 解析后的报告:", reportContent);

      // ✅ 确保数据是数组格式
      if (
        reportContent &&
        Array.isArray(reportContent.projects) &&
        reportContent.projects.length > 0
      ) {
        reportData.value = reportContent;
      } else {
        reportData.value = {
          settings: { useCompareMode: false },
          projects: [{ fields: JSON.parse(JSON.stringify(defaultFields)) }]
        };
      }

      reportId.value = response.data.reports[0].id;
      isEditing.value = true;
    }
  } catch (error) {
    console.error("進捗報告の取得失敗:", error);
  }
};

// ✅ 添加新的项目
const addNewProject = () => {
  reportData.value.projects.push({
    fields: JSON.parse(JSON.stringify(defaultFields))
  });
};

// ✅ 删除某个项目
const removeProject = (index) => {
  if (reportData.value.projects.length > 1) {
    reportData.value.projects.splice(index, 1);
  }
};

// ✅ 添加新的分类到某个项目
const addNewField = (projectIndex) => {
  const newFieldTitle = prompt("新しいカテゴリの名前を入力してください");
  if (newFieldTitle) {
    reportData.value.projects[projectIndex].fields.push({
      title: newFieldTitle,
      value: ""
    });
  }
};

// ✅ 提交报告（新建 or 更新）
const submitReport = async () => {
  if (!meeting_id) {
    snackbarText.value = "会議IDが無効です！";
    snackbarColor.value = "error";
    snackbar.value = true;
    return;
  }

  try {
    const reportJson = JSON.stringify(reportData.value);

    if (isEditing.value && reportId.value) {
      await api.put(`/api/meetings/${meeting_id}/reports/${reportId.value}`, { content: reportJson });
    } else {
      await api.post(`/api/meetings/${meeting_id}/newreport`, { content: reportJson });
    }

    snackbarText.value = isEditing.value ? "報告が更新されました！" : "報告が提出されました！";
    snackbarColor.value = "success";
    snackbar.value = true;

    setTimeout(() => {
      router.push(`/meeting/${meeting_id}`);
    }, 1500); // 少し表示してから遷移
  } catch (error) {
    console.error("進捗報告の提出に失敗しました:", error);
    snackbarText.value = "進捗報告の提出に失敗しました";
    snackbarColor.value = "error";
    snackbar.value = true;
  }
};

// ✅ 关闭按钮：返回会议详情页面
const closeAndReturn = () => {
  router.push(`/meeting/${meeting_id}`);
};

const parseContent = (content) => {
  if (!content) return { settings: {}, projects: [] };

  try {
    const parsed = typeof content === "string" ? JSON.parse(content) : content;

    // ✅ 新结构（带 settings 和 projects）
    if (parsed && Array.isArray(parsed.projects)) {
      return {
        settings: parsed.settings || {},
        projects: parsed.projects.map(p => ({
          fields: p.fields || []
        }))
      };
    }

    // ✅ 老结构（直接是 projects 数组）
    if (Array.isArray(parsed)) {
      return {
        settings: {},
        projects: parsed.map(p => ({
          fields: p.fields || []
        }))
      };
    }

    // fallback
    return { settings: {}, projects: [] };
  } catch (e) {
    console.error("❌ JSON 解析失败:", content);
    return { settings: {}, projects: [] };
  }
};

// ✅ 从后端获取最近一次的会议报告
const loadLastReport = async () => {
  try {
    const response = await api.get(`/api/reports/last/${user_id}`);

    if (response.data && response.data.report) {
      const lastReportContent = JSON.parse(response.data.report.content);
      console.log("📂 過去のレポート:", lastReportContent);

      // ✅ 使用 parseContent 兼容老/新格式
      const parsed = parseContent(lastReportContent);

      // ✅ 判断是否有内容（projects 非空）
      if (parsed.projects.length > 0) {
        reportData.value = {
          settings: parsed.settings,
          projects: parsed.projects
        };
      } else {
        reportData.value = {
          settings: { useCompareMode: false },
          projects: [{ fields: JSON.parse(JSON.stringify(defaultFields)) }]
        };
      }

      snackbarText.value = `履歴（会議ID: ${response.data.report.meeting_id}）が読み込まれました！`;
      snackbarColor.value = "success";
      snackbar.value = true;
    } else {
      snackbarText.value = `過去の報告は見つかりませんでした。`;
      snackbarColor.value = "error";
      snackbar.value = true;
    }
  } catch (error) {
    console.error("📂 最近のレポート取得失敗:", error);
    snackbarText.value = `履歴の取得に失敗しました。`;
    snackbarColor.value = "error";
    snackbar.value = true;
  }
};

const removeField = (projectIndex, fieldIndex) => {
  const fields = reportData.value.projects[projectIndex].fields;

  if (fields.length > 1) {
    fields.splice(fieldIndex, 1);
  } else {
    snackbarText.value = "最後のカテゴリは削除できません！";
    snackbarColor.value = "error";
    snackbar.value = true;
  }
};

// ✅ 组件加载时获取已有报告
onMounted(fetchExistingReport);

watchEffect(() => {
  showLastReportReadBtn.value = !isEditing.value;
});
</script>
