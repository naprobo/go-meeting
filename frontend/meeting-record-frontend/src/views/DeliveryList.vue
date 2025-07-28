<template>
    <v-container class="py-4">
        <v-snackbar
            v-model="snackbar"
            :color="snackbarColor"
            timeout="3000"
            location="bottom"
            >
            {{ snackbarMessage }}
        </v-snackbar>
      <v-overlay :model-value="loading" class="d-flex justify-center align-center" persistent>
        <v-progress-circular indeterminate size="64"></v-progress-circular>
      </v-overlay>
  
      <v-row align="center" justify="space-between">
        <h2>📦 納品管理</h2>
        <v-btn color="primary" @click="showMonthModal = true" prepend-icon="mdi-plus">月度追加</v-btn>
      </v-row>
  
      <v-divider class="my-4"></v-divider>
  
      <v-expansion-panels>
        <v-expansion-panel v-for="summary in deliverySummaries" :key="summary.id">
          <v-expansion-panel-title>
            <div class="d-flex justify-space-between align-center w-100">
              <span> {{ summary.delivery_month }} 納品</span>
              <div class="d-flex align-center">
                <v-tooltip text="詳細を追加" location="top">
                    <template #activator="{ props }">
                    <v-btn icon variant="text" v-bind="props" @click.stop="openDetailModal(summary.id, summary.delivery_month)">
                        <v-icon>mdi-plus</v-icon>
                    </v-btn>
                    </template>
                </v-tooltip>

                <v-tooltip text="前月プロジェクトをインポート" location="top">
                    <template #activator="{ props }">
                    <v-btn icon variant="text" v-bind="props" @click.stop="openImportDialog(summary.id, summary.delivery_month)">
                        <v-icon>mdi-database-import</v-icon>
                    </v-btn>
                    </template>
                </v-tooltip>
               </div>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-btn
                small
                variant="text"
                color="primary"
                class="mb-2"
                @click="toggleAllDetails(summary)"
            >
            {{
                summary.details.every(d => d.showExtra)
                ? 'すべて折りたたむ'
                : 'すべて展開'
            }}
            </v-btn>

            <v-table>
              <thead>
                <tr>
                  <th>📁 プロジェクト名</th>
                  <th>👤 担当者</th>
                  <th @click="toggleSort" class="cursor-pointer">
                    📅 納品日
                    <v-icon size="16" class="ml-1">
                        {{ sortOrder === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                    </v-icon>
                  </th>
                  <th>📌 状態</th>
                  <th>🚰 操作</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="detail in summary.details" :key="detail.id">
                  <tr :class="getRowClass(detail)">
                    <td>{{ detail.project_name }}</td>
                    <td>{{ detail.delivery_person || '未設定' }}</td>
                    <td>{{ formatDate(detail.delivery_date) }}</td>
                    <td>
                        <v-icon size="17" class="mr-1" v-if="detail.delivery_status === '納品物未作成'">mdi-progress-clock</v-icon>
                        <v-icon size="17" class="mr-1" v-else-if="detail.delivery_status === '納品物作成済'">mdi-file-document-check</v-icon>
                        <v-icon size="17" class="mr-1" v-else-if="detail.delivery_status === '納品済（送付済）'">mdi-truck-delivery</v-icon>
                        <v-icon size="17" class="mr-1" v-else-if="detail.delivery_status === '納品済（請求済）'">mdi-cash-check</v-icon>
                        <v-icon size="17" class="mr-1" v-else-if="detail.delivery_status === '遅延'">mdi-alert-circle</v-icon>
                        {{ detail.delivery_status }}
                    </td>
                    <td>
                        <template v-if="detail.created_by === user.id">
                            <v-icon size="20" color="primary" class="mr-2" @click="onEditDetail(detail, summary.id)">
                                mdi-pencil
                            </v-icon>
                            <v-icon size="20" color="red" @click="confirmDeleteDetail(detail.id, summary.id)">
                                mdi-delete
                            </v-icon>
                        </template>
                    </td>
                  </tr>
                  <tr v-if="detail.showExtra && hasExtraInfo(detail)">
                    <td colspan="6" class="pa-0" style="background-color: transparent;">
                        <v-card
                            class="mx-4 mb-2 pa-4 bg-grey-lighten-4"
                            elevation="0"
                            style="border-left: 4px solid var(--v-primary-base);"
                            >
                            <ul class="pl-0" style="list-style: none;">
                                <li v-if="detail.contract_number" class="d-flex align-center mb-1">
                                    <v-icon small class="mr-2">mdi-arrow-up-bold</v-icon>
                                    契約番号: {{ detail.contract_number }}
                                </li>
                                <li v-if="detail.contract_start || detail.contract_end" class="d-flex align-center">
                                    <v-icon small class="mr-2">mdi-calendar-range</v-icon>
                                    契約期間:
                                    <span v-if="detail.contract_start">{{ formatDate(detail.contract_start) }}</span>
                                    ～  
                                    <span v-if="detail.contract_end">{{ formatDate(detail.contract_end) }}</span>
                                </li>
                            </ul>
                        </v-card>
                    </td>
                  </tr>


                </template>
              </tbody>
            </v-table>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
  
      <v-dialog v-model="showMonthModal" max-width="400">
        <v-card>
          <v-card-title>月度を追加</v-card-title>
          <v-card-text>
            <v-text-field type="month" v-model="newMonth" label="納品月"></v-text-field>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="createSummary">作成</v-btn>
            <v-btn @click="showMonthModal = false">キャンセル</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-dialog v-model="confirmDeleteDialog" max-width="400">
        <v-card>
            <v-card-title>削除確認</v-card-title>
            <v-card-text>この納品情報を本当に削除しますか？</v-card-text>
            <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="red" @click="deleteDetail">削除</v-btn>
            <v-btn @click="confirmDeleteDialog = false">キャンセル</v-btn>
            </v-card-actions>
        </v-card>
      </v-dialog>

      <v-dialog v-model="showDetailModal" max-width="600">
        <v-card style="max-height: 90vh; display: flex; flex-direction: column;">
            <v-card-title>📁 納品詳細を追加</v-card-title>

            <!-- 滚动区 -->
            <v-card-text style="overflow-y: auto; flex: 1; padding-bottom: 16px;">
            <v-combobox
                label="プロジェクト名"
                v-model="detailForm.project_name"
                :items="projectCandidates.map(p => p.project_name)"
                @update:model-value="onProjectSelected"
                autocomplete="off"
            />
            <v-text-field label="納品担当者" v-model="detailForm.delivery_person" autocomplete="off"></v-text-field>
            <v-text-field label="納品日" type="date" v-model="detailForm.delivery_date"></v-text-field>
            <v-select
                label="状態"
                v-model="detailForm.delivery_status"
                :items="[
                '納品物未作成',
                '納品物作成済',
                '納品済（送付済）',
                '納品済（請求済）',
                '遅延'
                ]"
            />

            <v-expansion-panels multiple v-model="detailPanelIndexes">
                <v-expansion-panel>
                <v-expansion-panel-title>契約情報（未入力可）</v-expansion-panel-title>
                <v-expansion-panel-text>
                    <v-text-field label="契約番号" v-model="detailForm.contract_number" autocomplete="off"></v-text-field>
                    <v-text-field label="契約開始日" type="date" v-model="detailForm.contract_start" autocomplete="off"></v-text-field>
                    <v-text-field label="契約終了日" type="date" v-model="detailForm.contract_end" autocomplete="off"></v-text-field>
                </v-expansion-panel-text>
                </v-expansion-panel>

                <v-expansion-panel>
                <v-expansion-panel-title>請求金額情報（未入力可）</v-expansion-panel-title>
                <v-expansion-panel-text>
                    <v-select label="契約金額との差異" v-model="detailForm.overtime_cost_request" :items="['加算', '通常', '控除']"></v-select>
                    <v-row>
                    <v-col cols="4">
                        <v-text-field v-model="detailForm.base_hours_min" label="基準工数(最小H)" type="number" step="0.1"></v-text-field>
                    </v-col>
                    <v-col cols="4">
                        <v-text-field v-model="detailForm.base_hours_std" label="基準工数(標準H)" type="number" step="0.1"></v-text-field>
                    </v-col>
                    <v-col cols="4">
                        <v-text-field v-model="detailForm.base_hours_max" label="基準工数(最大H)" type="number" step="0.1"></v-text-field>
                    </v-col>
                    </v-row>
                </v-expansion-panel-text>
                </v-expansion-panel>

                <v-expansion-panel>
                <v-expansion-panel-title>メンバー情報（未入力可）</v-expansion-panel-title>
                <v-expansion-panel-text>
                    <v-btn small color="primary" @click="addMember">＋ メンバー追加</v-btn>
                    <div
                    v-for="(member, index) in detailForm.members"
                    :key="index"
                    class="mt-3 pa-2"
                    style="border: 1px solid #ccc; border-radius: 8px;"
                    >
                    <v-text-field v-model="member.member_name" autocomplete="off" label="メンバー名"></v-text-field>
                    <v-text-field v-model.number="member.unit_price" autocomplete="off" label="単価(円)" type="number"></v-text-field>
                    <v-text-field v-model.number="member.total_hours" autocomplete="off" label="当月工数(H)" type="number" step="0.01"></v-text-field>
                    <v-text-field v-model.number="member.work_ratio" autocomplete="off" label="当月人月数" type="number" step="0.01"></v-text-field>
                    </div>
                </v-expansion-panel-text>
                </v-expansion-panel>
            </v-expansion-panels>
            </v-card-text>

            <!-- 固定按钮 -->
            <v-card-actions style="border-top: 1px solid #eee;">
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="submitDetail">{{ editingDetailId ? '更新' : '追加' }}</v-btn>
            <v-btn @click="showDetailModal = false">キャンセル</v-btn>
            </v-card-actions>
        </v-card>
      </v-dialog>

      <v-dialog v-model="showImportDialog" max-width="900">
        <v-card>
            <v-card-title>📦 前月プロジェクトをインポート</v-card-title>
            <v-card-text>
            <v-table>
                <thead>
                <tr>
                    <th></th>
                    <th>プロジェクト名</th>
                    <th>担当者</th>
                    <th>契約番号</th>
                    <th>契約期間</th>
                    <th>納品日</th>
                </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="(record, index) in importCandidates"
                        :key="index"
                        :class="{ 'text-grey': isContractAlreadyImported(record.contract_number), 'opacity-50': isContractAlreadyImported(record.contract_number) }"
                        style="vertical-align: middle;"
                    >
                        <td style="vertical-align: middle;">
                            <v-checkbox
                                v-model="record.checked"
                                :disabled="isContractAlreadyImported(record.contract_number)"
                                density="compact"
                                style="display: flex; align-items: center; justify-content: center;"
                            />
                        </td>
                        <td style="vertical-align: middle;">{{ record.project_name }}</td>
                        <td style="vertical-align: middle;">{{ record.delivery_person }}</td>
                        <td style="vertical-align: middle;">{{ record.contract_number }}</td>
                        <td style="vertical-align: middle;">
                            <span v-if="record.contract_start || record.contract_end">
                            {{ record.contract_start ? formatDate(record.contract_start) : '' }}
                            ～
                            {{ record.contract_end ? formatDate(record.contract_end) : '' }}
                            </span>
                        </td>
                        <td style="vertical-align: middle;">
                            <v-text-field
                                v-model="record.delivery_date"
                                type="date"
                                density="compact"
                                hide-details
                                style="max-width: 180px; min-width: 120px;"
                                :readonly="isContractAlreadyImported(record.contract_number)"
                            />
                        </td>
                    </tr>
                </tbody>
            </v-table>
            </v-card-text>
            <v-card-actions>
            <v-spacer />
            <v-btn color="primary" @click="submitImports">インポート</v-btn>
            <v-btn @click="showImportDialog = false">キャンセル</v-btn>
            </v-card-actions>
        </v-card>
      </v-dialog>

    </v-container>
</template>
  

<script setup>
  import { ref, computed, onMounted } from "vue";
  import { useAuthStore } from "@/store";
  import api from "@/api";
  
  const authStore = useAuthStore();
  const user = computed(() => authStore.user);
  
  const loading = ref(false);
  const deliverySummaries = ref([]);
  const showMonthModal = ref(false);
  const showDetailModal = ref(false);
  const confirmDeleteDialog = ref(false);
  const newMonth = ref("");
  const currentSummaryId = ref(null);
  const currentSummaryMonth = ref("");
  const editingDetailId = ref(null);
  const deleteTarget = ref({ id: null, summaryId: null });
  const projectCandidates = ref([]);

  const showImportDialog = ref(false);
  const importCandidates = ref([]);

  const snackbar = ref(false);
  const snackbarMessage = ref('');
  const snackbarColor = ref('info');

  const detailPanelIndexes = ref([0]); // 默认展开第一个契約情報面板

  const showSnackbar = (message, color = 'info') => {
    snackbarMessage.value = message;
    snackbarColor.value = color;
    snackbar.value = true;
  };

  // 初期化用常量
  const defaultBaseHours = {
    base_hours_min: 140,
    base_hours_std: 160,
    base_hours_max: 180
  };
  
  const detailForm = ref({
    project_name: "",
    delivery_person: "",
    delivery_date: new Date().toISOString().split("T")[0],
    delivery_status: "納品物未作成",
    contract_number: null,
    contract_start: null,
    contract_end: null,
    overtime_cost_request: "通常",
    ...defaultBaseHours,
    members: []
  });
  
  const addMember = () => {
    detailForm.value.members.push({
      member_name: "",
      unit_price: null,
      total_hours: null,
      work_ratio: 1.0
    });
  };
  
  const sortDetails = (details, order = 'asc') => {
    return [...details].sort((a, b) => {
        const dateA = new Date(a.delivery_date);
        const dateB = new Date(b.delivery_date);
        if (dateA.getTime() !== dateB.getTime()) {
        return order === 'asc' ? dateA - dateB : dateB - dateA;
        }

        // 納品日相同時，按 delivery_person 排序
        const nameA = (a.delivery_person || '').toLowerCase();
        const nameB = (b.delivery_person || '').toLowerCase();
        if (nameA < nameB) return -1;
        if (nameA > nameB) return 1;
        return 0;
    });
  };

  const fetchDeliverySummaries = async () => {
    loading.value = true;
    try {
        const res = await api.get("/api/delivery/months");
        const summaries = await Promise.all(
        res.data.map(async (summary) => {
            const detailRes = await api.get(`/api/delivery/${summary.id}`);
            const rawDetails = detailRes.data.map((d) => ({ ...d, showExtra: false }));
            const sortedDetails = sortDetails(rawDetails, sortOrder.value);
            return { ...summary, details: sortedDetails };
        })
        );
        deliverySummaries.value = summaries.sort((a, b) =>
        a.delivery_month.localeCompare(b.delivery_month)
        );
    } finally {
        loading.value = false;
    }
  };

  
  const createSummary = async () => {
    if (!newMonth.value) {
        showSnackbar("納品月を入力してください", "warning");
        return;
    }
    loading.value = true;
    try {
      await api.post("/api/delivery/newsummaries", {
        delivery_month: newMonth.value
      });
      showMonthModal.value = false;
      newMonth.value = "";
      await fetchDeliverySummaries();
    } finally {
      loading.value = false;
    }
  };
  
  const openDetailModal = (summaryId, summaryMonth) => {
    currentSummaryId.value = summaryId;
    currentSummaryMonth.value = summaryMonth;

    // 重置展开状态（只展开第一个 panel）
    detailPanelIndexes.value = [0];

    // 初始化 form
    detailForm.value = {
        project_name: "",
        delivery_person: "",
        delivery_date: new Date().toISOString().split("T")[0],
        delivery_status: "納品物未作成",
        contract_number: null,
        contract_start: null,
        contract_end: null,
        overtime_cost_request: "通常",
        ...defaultBaseHours,
        members: []
    };
    editingDetailId.value = null;

    // 候補プロジェクト探す（最大12ヶ月前まで）
    const targetDate = new Date(`${summaryMonth}-01`);
    let found = false;

    for (let i = 1; i <= 12; i++) {
        const searchDate = new Date(targetDate);
        searchDate.setMonth(searchDate.getMonth() - i);
        const searchMonthStr = `${searchDate.getFullYear()}-${String(searchDate.getMonth() + 1).padStart(2, "0")}`;

        const prevSummary = deliverySummaries.value.find(s => s.delivery_month === searchMonthStr);
        if (!prevSummary) continue;

        const candidates = prevSummary.details.filter(d => d.created_by === user.value.id);
        if (candidates.length > 0) {
        projectCandidates.value = candidates;
        found = true;
        break;
        }
    }

    if (!found) {
        projectCandidates.value = [];
    }

    showDetailModal.value = true;
  };


  const onProjectSelected = (projectName) => {
    const matched = projectCandidates.value.find(p => p.project_name === projectName);
    if (matched) {
        detailForm.value.delivery_person = matched.delivery_person;
        detailForm.value.delivery_date = formatDateOnly(matched.delivery_date);
        detailForm.value.delivery_status = "納品物未作成";
        detailForm.value.contract_number = matched.contract_number;
        detailForm.value.contract_start = formatDateOnly(matched.contract_start);
        detailForm.value.contract_end = formatDateOnly(matched.contract_end);
        detailForm.value.overtime_cost_request = matched.overtime_cost_request;
        detailForm.value.base_hours_min = matched.base_hours_min ?? 140;
        detailForm.value.base_hours_std = matched.base_hours_std ?? 160;
        detailForm.value.base_hours_max = matched.base_hours_max ?? 180;
        detailForm.value.members = matched.members?.map(m => ({ ...m })) || [];
    }
  };

  
  const formatDateOnly = (value) => {
    return value ? value.substring(0, 10) : null;
  };

  const editDetail = (detail, summaryId) => {
    currentSummaryId.value = summaryId;
    detailForm.value = {
      project_name: detail.project_name,
      delivery_person: detail.delivery_person,
      delivery_date: formatDateOnly(detail.delivery_date),
      delivery_status: detail.delivery_status,
      contract_number: detail.contract_number,
      contract_start: formatDateOnly(detail.contract_start),
      contract_end: formatDateOnly(detail.contract_end),
      overtime_cost_request: detail.overtime_cost_request,
      base_hours_min: detail.base_hours_min ?? 140,
      base_hours_std: detail.base_hours_std ?? 160,
      base_hours_max: detail.base_hours_max ?? 180,
      members: detail.members || []
    };
    editingDetailId.value = detail.id;
    showDetailModal.value = true;
  };
  
  const onEditDetail = (detail, summaryId) => {
    if (detail.created_by === user.value?.id) {
      editDetail(detail, summaryId);
    }
  };
  
  const confirmDeleteDetail = (id, summaryId) => {
    deleteTarget.value = { id, summaryId };
    confirmDeleteDialog.value = true;
  };
  
    const onDeleteDetail = (id, summaryId) => {
        const summary = deliverySummaries.value.find((s) => s.id === summaryId);
        const detail = summary?.details.find((d) => d.id === id);
        if (detail && detail.created_by === user.value?.id) {
        confirmDeleteDetail(id, summaryId);
        }
    };
  
    const deleteDetail = async () => {
    loading.value = true;
    try {
        const { id } = deleteTarget.value;
        await api.delete(`/api/delivery/details/${id}`);
        confirmDeleteDialog.value = false;
        await fetchDeliverySummaries();
    } finally {
        loading.value = false;
    }
    };

    const submitDetail = async () => {
        const form = detailForm.value;

        if (!form.project_name?.trim()) {
            showSnackbar("プロジェクト名は必須です", "warning");
            return;
        }
        if (!form.delivery_date) {
            showSnackbar("納品日を入力してください", "warning");
            return;
        }
        if (!form.delivery_status) {
            showSnackbar("状態を選択してください", "warning");
            return;
        }

        loading.value = true;
        try {
            const payload = {
                ...detailForm.value,
                delivery_date: formatDateOnly(detailForm.value.delivery_date),
                contract_start: formatDateOnly(detailForm.value.contract_start),
                contract_end: formatDateOnly(detailForm.value.contract_end)
            };
            if (editingDetailId.value) {
                await api.put(`/api/delivery/details/${editingDetailId.value}`, payload);
            } else {
                await api.post(`/api/delivery/summaries/${currentSummaryId.value}/details`, payload);
            }
            showDetailModal.value = false;
            editingDetailId.value = null;
            await fetchDeliverySummaries();
        } finally {
            loading.value = false;
        }
    };

    const formatDate = (date) => {
        if (!date) return "";
        const d = new Date(date);
        if (isNaN(d.getTime())) return "";
        return d.toLocaleDateString("ja-JP");
    };

  const getRowClass = (detail) => {
    const today = new Date();
    const deliveryDate = new Date(detail.delivery_date);
    const diffDays = Math.ceil((deliveryDate - today) / (1000 * 60 * 60 * 24));
    const status = detail.delivery_status;

    switch (status) {
        case '納品済（請求済）':
            return 'bg-success text-white'; // 完全完成：深绿色
        case '納品済（送付済）':
            return 'bg-green-lighten-4'; // 淡绿色
        case '遅延':
            return 'bg-error text-white'; // 红色
        case '納品物作成済':
            if (diffDays <= 0) {
                return 'bg-error text-white';
            }
            if (diffDays > 0 && diffDays <= 5) {
                return 'bg-orange-lighten-1 text-white'; // 5天内 = 浅黄色
            }
            return '';
        case '納品物未作成':
            if (diffDays <= 0) {
                return 'bg-error text-white';
            }
            if (diffDays > 0 && diffDays <= 5) {
                return 'bg-warning text-white'; // 5天内 = 黄色
            }
            return '';
        default:
            return '';
    }
  };

  const toggleAllDetails = (summary) => {
    const allExpanded = summary.details.every((d) => d.showExtra);
    summary.details.forEach((d) => {
        d.showExtra = !allExpanded;
    });
  };

  const sortOrder = ref('asc');

  const toggleSort = () => {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
    deliverySummaries.value.forEach(summary => {
        summary.details = sortDetails(summary.details, sortOrder.value);
    });
  };
  
  const hasExtraInfo = (detail) => {
    return !!(
        detail.contract_number ||
        detail.contract_start ||
        detail.contract_end
        // 可以追加其他如 detail.overtime_cost_request 等字段
    );
  };

  const openImportDialog = (summaryId, summaryMonth) => {
    currentSummaryId.value = summaryId;
    currentSummaryMonth.value = summaryMonth;

    const targetDate = new Date(`${summaryMonth}-01`);
    const maxSearchBackMonths = 12; // 最多往前找12个月
    let found = false;

    for (let i = 1; i <= maxSearchBackMonths; i++) {
        const searchDate = new Date(targetDate);
        searchDate.setMonth(searchDate.getMonth() - i);
        const prevMonthStr = `${searchDate.getFullYear()}-${String(searchDate.getMonth() + 1).padStart(2, "0")}`;

        const prevSummary = deliverySummaries.value.find(s => s.delivery_month === prevMonthStr);
        if (!prevSummary) continue;

        const candidates = prevSummary.details.filter(d => d.created_by === user.value.id);
        if (candidates.length > 0) {
        const currentContracts = new Set(
            deliverySummaries.value.find(s => s.delivery_month === summaryMonth)
            ?.details.map(d => d.contract_number).filter(Boolean)
        );

        importCandidates.value = candidates.map(d => ({
            ...d,
            checked: !d.contract_number || !currentContracts.has(d.contract_number),
            delivery_date: new Date().toISOString().split("T")[0]
        }));

        found = true;
        break;
        }
    }

    if (!found) {
        showSnackbar("過去の月にも自分が作成したデータが見つかりませんでした", "warning");
        return;
    }

    showImportDialog.value = true;
  };


    const isContractAlreadyImported = (contractNumber) => {
        if (!contractNumber) return false;
        const summary = deliverySummaries.value.find(s => s.delivery_month === currentSummaryMonth.value);
        return summary?.details.some(d => d.contract_number === contractNumber);
    };

    const submitImports = async () => {
        const selected = importCandidates.value.filter(d => d.checked);
        if (selected.length === 0) {
            showSnackbar("インポート対象が選択されていません", "warning");
            return;
        }

        loading.value = true;
        try {
            for (const d of selected) {
            const payload = {
                project_name: d.project_name,
                delivery_person: d.delivery_person,
                delivery_date: formatDateOnly(d.delivery_date),
                delivery_status: "納品物未作成",
                contract_number: d.contract_number,
                contract_start: formatDateOnly(d.contract_start),
                contract_end: formatDateOnly(d.contract_end),
                overtime_cost_request: d.overtime_cost_request ?? "通常",
                base_hours_min: d.base_hours_min ?? 140,
                base_hours_std: d.base_hours_std ?? 160,
                base_hours_max: d.base_hours_max ?? 180,
                members: d.members?.map(m => ({ ...m })) || []
            };
            await api.post(`/api/delivery/summaries/${currentSummaryId.value}/details`, payload);
            }
            showSnackbar("インポート完了", "success");
            showImportDialog.value = false;
            await fetchDeliverySummaries();
        } finally {
            loading.value = false;
        }
    };
  onMounted(fetchDeliverySummaries);
</script>
  
  <style scoped>
  .v-expansion-panel-title {
    font-weight: bold;
    font-size: 16px;
  }
  .v-icon--disabled {
    pointer-events: none;
    opacity: 0.4;
  }
  </style>
  