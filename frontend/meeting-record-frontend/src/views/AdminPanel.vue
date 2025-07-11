<template>
  <v-container class="py-6">
    <v-card elevation="2" class="pa-4">
      <v-card-title>
        <h2 class="text-h5">👮‍♂️ 管理者コントロールパネル</h2>
      </v-card-title>

      <!-- ✅ 用户列表 -->
      <v-data-table
        :headers="headers"
        :items="users"
        item-value="id"
        class="elevation-1"
        dense
      >
        <template #item.group="{ item }">
          <v-select
            v-model="item.group"
            :items="['Member', 'Leader', 'Admin']"
            density="compact"
            hide-details
            style="min-width: 120px"
            @update:modelValue="() => updateUserGroup(item)"
          ></v-select>
        </template>

        <template #item.is_approved="{ item }">
          <v-btn
            :color="item.is_approved ? 'success' : 'error'"
            variant="outlined"
            @click="toggleApproval(item)"
          >
            {{ item.is_approved ? '✔ 承認済' : '✖ 未承認' }}
          </v-btn>
        </template>

        <template #item.is_active="{ item }">
          <v-btn
            :color="item.is_active ? 'info' : 'warning'"
            variant="outlined"
            @click="toggleActive(item)"
          >
            {{ item.is_active ? '✅ 有効' : '🚫 無効' }}
          </v-btn>
        </template>

        <template #item.actions="{ item }">
          <v-btn color="error" @click="deleteUser(item.id)" icon>
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>

      <v-btn class="mt-4" color="secondary" @click="goBack">
        ⬅ 戻る
      </v-btn>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

const users = ref([]);
const router = useRouter();

const headers = [
  { text: "ユーザーID", value: "username" },
  { text: "氏名", value: "fullname" },
  { text: "グループ", value: "group" },
  { text: "承認済み", value: "is_approved" },
  { text: "アクティブ", value: "is_active" },
  { text: "アクション", value: "actions", sortable: false },
];

const fetchUsers = async () => {
  try {
    const response = await api.get("/api/admin/users");
    users.value = response.data;
  } catch (error) {
    console.error("ユーザー一覧の取得に失敗:", error);
  }
};

const toggleApproval = async (user) => {
  try {
    await api.put(`/api/admin/users/${user.id}/approve`, {
      is_approved: !user.is_approved,
    });
    user.is_approved = !user.is_approved;
  } catch (error) {
    console.error("承認の更新失敗:", error);
  }
};

const toggleActive = async (user) => {
  try {
    await api.put(`/api/admin/users/${user.id}/disable`, {
      is_active: !user.is_active,
    });
    user.is_active = !user.is_active;
  } catch (error) {
    console.error("アクティブの更新失敗:", error);
  }
};

const updateUserGroup = async (user) => {
  try {
    await api.put(`/api/admin/users/${user.id}/group`, {
      new_group: user.group,
    });
  } catch (error) {
    console.error("グループ変更失敗:", error);
  }
};

const deleteUser = async (userId) => {
  if (confirm("本当に削除しますか？")) {
    try {
      await api.delete(`/api/admin/users/${userId}`);
      users.value = users.value.filter((user) => user.id !== userId);
    } catch (error) {
      console.error("ユーザー削除失敗:", error);
    }
  }
};

const goBack = () => {
  router.push("/");
};

onMounted(fetchUsers);
</script>
