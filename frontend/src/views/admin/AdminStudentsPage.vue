<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { useAdminStudentsStore } from '@/stores/adminStudents'
import type { AdminStudent } from '@/types/api'

const studentsStore = useAdminStudentsStore()

const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const createForm = reactive({ username: '', nickname: '', password: '' })
const editForm = reactive({ userId: 0, nickname: '', new_password: '' })

function resetCreateForm() {
  createForm.username = ''
  createForm.nickname = ''
  createForm.password = ''
}

function openCreateDialog() {
  resetCreateForm()
  createDialogVisible.value = true
}

function openEditDialog(student: AdminStudent) {
  editForm.userId = student.user_id
  editForm.nickname = student.nickname
  editForm.new_password = ''
  editDialogVisible.value = true
}

async function openStudentDetail(userId: number) {
  detailDrawerVisible.value = true
  await studentsStore.loadStudentDetail(userId)
}

function handleRowClick(row: AdminStudent) {
  void openStudentDetail(row.user_id)
}

async function handleCreateStudent() {
  try {
    await studentsStore.createStudentAccount(createForm)
    createDialogVisible.value = false
    resetCreateForm()
    ElMessage.success('学生账号已创建。')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '创建学生失败。')
  }
}

async function handleUpdateStudent() {
  try {
    await studentsStore.updateStudentAccount(editForm.userId, editForm)
    editDialogVisible.value = false
    ElMessage.success('学生信息已更新。')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新学生失败。')
  }
}

async function handleDisableStudent(student: AdminStudent) {
  try {
    await ElMessageBox.confirm(
      `确定要禁用学生“${student.nickname}”吗？禁用后该账号将无法继续登录。`,
      '禁用学生账号',
      {
        confirmButtonText: '确认禁用',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await studentsStore.disableStudentAccount(student.user_id)
    ElMessage.success('学生账号已禁用。')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error instanceof Error ? error.message : '禁用学生失败。')
  }
}

onMounted(() => {
  void studentsStore.loadStudents()
})
</script>

<template>
  <section class="admin-page">
    <div class="admin-page__heading">
      <div>
        <p>Students</p>
        <h2>学生管理</h2>
      </div>
      <div class="admin-page__actions">
        <el-button :icon="Refresh" :loading="studentsStore.loading" @click="studentsStore.loadStudents">
          刷新
        </el-button>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增学生</el-button>
      </div>
    </div>

    <el-alert
      v-if="studentsStore.error"
      class="admin-page__alert"
      :title="studentsStore.error"
      type="error"
      show-icon
      :closable="false"
    />

    <el-card shadow="never" class="admin-students-card">
      <div class="admin-toolbar">
        <el-input
          v-model.trim="studentsStore.search"
          :prefix-icon="Search"
          placeholder="搜索用户名或昵称"
          clearable
          @keyup.enter="studentsStore.applyFilters"
        />
        <el-select v-model="studentsStore.status" placeholder="状态" @change="studentsStore.applyFilters">
          <el-option label="仅启用" value="active" />
          <el-option label="全部学生" value="all" />
          <el-option label="仅禁用" value="disabled" />
        </el-select>
        <el-select v-model="studentsStore.sortBy" placeholder="排序依据" @change="studentsStore.applyFilters">
          <el-option label="总分" value="total_score" />
          <el-option label="正确率" value="accuracy" />
          <el-option label="作答量" value="total_questions" />
        </el-select>
        <el-select v-model="studentsStore.order" placeholder="排序方向" @change="studentsStore.applyFilters">
          <el-option label="从高到低" value="desc" />
          <el-option label="从低到高" value="asc" />
        </el-select>
        <el-button type="primary" @click="studentsStore.applyFilters">查询</el-button>
      </div>

      <el-table
        v-loading="studentsStore.loading"
        :data="studentsStore.filteredStudents"
        border
        row-key="user_id"
        empty-text="暂无学生数据"
        @row-click="handleRowClick"
      >
        <el-table-column label="学生" min-width="180">
          <template #default="{ row }">
            <div class="student-cell">
              <strong>{{ row.nickname }}</strong>
              <span>@{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="总分" width="110">
          <template #default="{ row }">{{ studentsStore.formatNumber(row.total_score) }}</template>
        </el-table-column>
        <el-table-column label="战力" width="110">
          <template #default="{ row }">{{ studentsStore.formatNumber(row.power_score) }}</template>
        </el-table-column>
        <el-table-column label="正确率" width="110">
          <template #default="{ row }">{{ studentsStore.formatPercent(row.accuracy) }}</template>
        </el-table-column>
        <el-table-column label="作答量" width="110">
          <template #default="{ row }">{{ studentsStore.formatNumber(row.total_questions) }}</template>
        </el-table-column>
        <el-table-column label="最近活跃" min-width="150">
          <template #default="{ row }">{{ studentsStore.formatDateTime(row.last_active) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="View" @click.stop="openStudentDetail(row.user_id)">详情</el-button>
            <el-button link :icon="Edit" @click.stop="openEditDialog(row)">编辑</el-button>
            <el-button
              link
              type="danger"
              :disabled="!row.is_active"
              @click.stop="handleDisableStudent(row)"
            >
              禁用
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="admin-table-footer">
        <span>共 {{ studentsStore.formatNumber(studentsStore.total) }} 位学生</span>
        <div>
          <el-button :disabled="!studentsStore.hasPreviousPage" @click="studentsStore.goPreviousPage">上一页</el-button>
          <el-button :disabled="!studentsStore.hasNextPage" @click="studentsStore.goNextPage">下一页</el-button>
        </div>
      </div>
    </el-card>

    <el-drawer v-model="detailDrawerVisible" title="学生详情" size="420px">
      <el-skeleton v-if="studentsStore.detailLoading" :rows="8" animated />
      <template v-else-if="studentsStore.studentDetail">
        <div class="student-detail">
          <div class="student-detail__profile">
            <div>
              <strong>{{ studentsStore.studentDetail.nickname }}</strong>
              <span>@{{ studentsStore.studentDetail.username }}</span>
            </div>
            <el-tag :type="studentsStore.studentDetail.is_active ? 'success' : 'info'">
              {{ studentsStore.studentDetail.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </div>

          <div class="student-detail__metrics">
            <article>
              <span>总作答</span>
              <strong>{{ studentsStore.formatNumber(studentsStore.studentDetail.total_questions) }}</strong>
            </article>
            <article>
              <span>正确率</span>
              <strong>{{ studentsStore.studentAccuracy }}</strong>
            </article>
            <article>
              <span>总分</span>
              <strong>{{ studentsStore.formatNumber(studentsStore.studentDetail.total_score) }}</strong>
            </article>
            <article>
              <span>总战力</span>
              <strong>{{ studentsStore.formatNumber(studentsStore.studentDetail.power_score) }}</strong>
            </article>
          </div>

          <div class="student-detail__actions" v-if="studentsStore.selectedStudent">
            <el-button @click="openEditDialog(studentsStore.selectedStudent)">编辑资料</el-button>
            <el-button
              type="danger"
              :disabled="!studentsStore.selectedStudent.is_active"
              @click="handleDisableStudent(studentsStore.selectedStudent)"
            >
              禁用账号
            </el-button>
          </div>

          <el-divider content-position="left">关卡战力拆解</el-divider>
          <el-empty
            v-if="studentsStore.studentDetail.level_breakdown.length === 0"
            description="暂无关卡表现数据"
          />
          <div v-else class="student-detail__levels">
            <article
              v-for="row in studentsStore.studentDetail.level_breakdown"
              :key="`${row.level_id}-${row.level_name}`"
            >
              <strong>{{ row.unit_name }} / {{ row.level_name }}</strong>
              <span>
                总战力 {{ row.total }} · 通关 {{ row.clear }} · 满分 {{ row.perfect }} ·
                速度 {{ row.speed }} · 连击 {{ row.combo }}
              </span>
            </article>
          </div>
        </div>
      </template>
      <el-empty v-else description="请选择一个学生查看详情" />
    </el-drawer>

    <el-dialog v-model="createDialogVisible" title="新增学生" width="420px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model.trim="createForm.username" autocomplete="off" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model.trim="createForm.nickname" autocomplete="off" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="createForm.password" autocomplete="new-password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="studentsStore.saving" @click="handleCreateStudent">
          创建学生
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑学生" width="420px">
      <el-form :model="editForm" label-position="top">
        <el-form-item label="昵称">
          <el-input v-model.trim="editForm.nickname" autocomplete="off" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="editForm.new_password" type="password" autocomplete="new-password" placeholder="留空则不修改" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="studentsStore.saving" @click="handleUpdateStudent">
          保存修改
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.admin-page__heading,
.admin-page__actions,
.admin-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.admin-page__heading {
  margin-bottom: 18px;
}

.admin-page__actions {
  justify-content: flex-end;
}

.admin-page__heading p {
  margin: 0 0 4px;
  color: var(--admin-primary);
  font-size: 13px;
}

.admin-page__heading h2 {
  margin: 0;
  font-size: 26px;
}

.admin-page__alert {
  margin-bottom: 16px;
}

.admin-students-card {
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
}

.admin-toolbar {
  flex-wrap: wrap;
  justify-content: flex-start;
  margin-bottom: 14px;
}

.admin-toolbar .el-input {
  max-width: 280px;
}

.admin-toolbar .el-select {
  max-width: 160px;
}

.student-cell {
  display: grid;
  gap: 2px;
}

.student-cell strong {
  color: var(--admin-text);
}

.student-cell span {
  color: var(--admin-muted);
  font-size: 12px;
}

.admin-table-footer {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  color: var(--admin-muted);
  font-size: 14px;
}

.student-detail {
  display: grid;
  gap: 18px;
}

.student-detail__profile,
.student-detail__actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.student-detail__profile strong,
.student-detail__profile span {
  display: block;
}

.student-detail__profile strong {
  color: var(--admin-text);
  font-size: 20px;
}

.student-detail__profile span {
  color: var(--admin-muted);
}

.student-detail__metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.student-detail__metrics article {
  padding: 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
}

.student-detail__metrics span,
.student-detail__metrics strong {
  display: block;
}

.student-detail__metrics span {
  color: var(--admin-muted);
  font-size: 12px;
}

.student-detail__metrics strong {
  margin-top: 6px;
  color: var(--admin-text);
  font-size: 22px;
}

.student-detail__levels {
  display: grid;
  max-height: 320px;
  gap: 10px;
  overflow: auto;
  padding-right: 4px;
}

.student-detail__levels article {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
}

.student-detail__levels strong {
  color: var(--admin-text);
}

.student-detail__levels span {
  color: var(--admin-muted);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 760px) {
  .admin-page__heading,
  .admin-table-footer,
  .student-detail__profile,
  .student-detail__actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
