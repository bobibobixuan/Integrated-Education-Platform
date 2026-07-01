<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Plus, Refresh, Search, UploadFilled, View } from '@element-plus/icons-vue'
import { useAdminQuestionsStore } from '@/stores/adminQuestions'
import type { AdminQuestion } from '@/types/api'

const questionsStore = useAdminQuestionsStore()
const editorVisible = ref(false)
const detailVisible = ref(false)
const jsonUploadRef = ref()
const excelUploadRef = ref()

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

function openCreateEditor() {
  questionsStore.openNewQuestionForm()
  editorVisible.value = true
}

function openEditEditor(question: AdminQuestion) {
  questionsStore.openEditQuestionForm(question)
  editorVisible.value = true
}

function openQuestionDetail(question: AdminQuestion) {
  questionsStore.selectedQuestionId = question.id
  detailVisible.value = true
}

function handleRowClick(row: AdminQuestion) {
  openQuestionDetail(row)
}

async function saveQuestion() {
  try {
    const isEditing = questionsStore.editingQuestionId !== null
    await questionsStore.saveQuestion()
    editorVisible.value = false
    ElMessage.success(isEditing ? '题目已更新。' : '题目已创建。')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

async function confirmToggleQuestion(question: AdminQuestion) {
  try {
    await ElMessageBox.confirm(
      question.is_active ? '禁用后该题目不会继续出现在学生端。' : '启用后该题目会重新参与出题。',
      question.is_active ? '禁用题目' : '启用题目',
      {
        confirmButtonText: question.is_active ? '确认禁用' : '确认启用',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await questionsStore.toggleQuestionActive(question)
    ElMessage.success(`题目已${question.is_active ? '禁用' : '启用'}。`)
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(getErrorMessage(error))
  }
}

async function handleJsonUpload(uploadFile: { raw?: File }) {
  if (!uploadFile.raw) return
  try {
    await questionsStore.fillJsonFromFile(uploadFile.raw)
    ElMessage.success('JSON 文件内容已填入文本框。')
  } catch {
    ElMessage.error('读取 JSON 文件失败。')
  } finally {
    jsonUploadRef.value?.clearFiles?.()
  }
}

function handleExcelUpload(uploadFile: { raw?: File }) {
  if (!uploadFile.raw) return
  questionsStore.setExcelFile(uploadFile.raw)
  excelUploadRef.value?.clearFiles?.()
}

async function submitJsonImport() {
  try {
    const message = await questionsStore.importJsonQuestions()
    ElMessage.success(message)
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

async function submitExcelImport() {
  try {
    const message = await questionsStore.importExcelQuestions()
    ElMessage.success(message)
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

async function handleUnitFilterChange(value: number) {
  questionsStore.setUnitFilter(value)
  await questionsStore.applyFilters()
}

onMounted(() => {
  void questionsStore.loadQuestions()
})
</script>

<template>
  <section class="admin-page">
    <div class="admin-page__heading">
      <div>
        <p>Questions</p>
        <h2>题库管理</h2>
      </div>
      <div class="admin-page__actions">
        <el-button :icon="Refresh" :loading="questionsStore.loading" @click="questionsStore.loadQuestions">
          刷新
        </el-button>
        <el-button type="primary" :icon="Plus" @click="openCreateEditor">新建题目</el-button>
      </div>
    </div>

    <el-alert
      v-if="questionsStore.error"
      class="admin-page__alert"
      :title="questionsStore.error"
      type="error"
      show-icon
      :closable="false"
    />

    <el-card shadow="never" class="admin-questions-card">
      <el-tabs v-model="questionsStore.activeTab">
        <el-tab-pane label="题目列表" name="list">
          <div class="admin-toolbar">
            <el-input
              v-model.trim="questionsStore.search"
              :prefix-icon="Search"
              placeholder="搜索题干 / 知识点"
              clearable
              @keyup.enter="questionsStore.applyFilters"
            />
            <el-select v-model="questionsStore.unitId" placeholder="单元" @change="handleUnitFilterChange">
              <el-option label="全部单元" :value="0" />
              <el-option v-for="unit in questionsStore.units" :key="unit.id" :label="unit.name" :value="unit.id" />
            </el-select>
            <el-select v-model="questionsStore.levelId" placeholder="关卡" @change="questionsStore.applyFilters">
              <el-option label="全部关卡" :value="0" />
              <el-option
                v-for="option in questionsStore.filteredLevelOptions"
                :key="option.levelId"
                :label="option.label"
                :value="option.levelId"
              />
            </el-select>
            <el-select v-model="questionsStore.questionType" placeholder="题型" @change="questionsStore.applyFilters">
              <el-option label="全部题型" value="" />
              <el-option label="选择题" value="选择题" />
              <el-option label="多选题" value="多选题" />
              <el-option label="判断题" value="判断题" />
              <el-option label="填空题" value="填空题" />
            </el-select>
            <el-select v-model="questionsStore.status" placeholder="状态" @change="questionsStore.applyFilters">
              <el-option label="仅启用" value="active" />
              <el-option label="全部题目" value="all" />
              <el-option label="仅停用" value="inactive" />
            </el-select>
            <el-button type="primary" @click="questionsStore.applyFilters">查询</el-button>
          </div>

          <el-table
            v-loading="questionsStore.loading"
            :data="questionsStore.filteredQuestions"
            border
            row-key="id"
            empty-text="暂无题目数据"
            @row-click="handleRowClick"
          >
            <el-table-column label="ID" width="90">
              <template #default="{ row }">#{{ row.id }}</template>
            </el-table-column>
            <el-table-column label="题目" min-width="260">
              <template #default="{ row }">
                <div class="question-cell">
                  <strong>{{ row.title || '未命名题目' }}</strong>
                  <span>{{ row.content }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="题型" width="110" />
            <el-table-column prop="unit_name" label="单元" min-width="140" />
            <el-table-column prop="level_name" label="关卡" min-width="140" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="210" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" :icon="View" @click.stop="openQuestionDetail(row)">详情</el-button>
                <el-button link :icon="Edit" @click.stop="openEditEditor(row)">编辑</el-button>
                <el-button link :type="row.is_active ? 'danger' : 'success'" @click.stop="confirmToggleQuestion(row)">
                  {{ row.is_active ? '停用' : '启用' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="admin-table-footer">
            <span>共 {{ questionsStore.formatNumber(questionsStore.total) }} 题</span>
            <div>
              <el-button :disabled="!questionsStore.hasPreviousPage" @click="questionsStore.goPreviousPage">上一页</el-button>
              <el-button :disabled="!questionsStore.hasNextPage" @click="questionsStore.goNextPage">下一页</el-button>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="导入中心" name="import">
          <el-row :gutter="16">
            <el-col :xs="24" :lg="12">
              <el-card shadow="never" class="import-card">
                <template #header>
                  <div class="card-head">
                    <strong>JSON 导入</strong>
                    <span>支持上传 `.json` 文件，也支持直接粘贴文本。</span>
                  </div>
                </template>

                <el-upload
                  ref="jsonUploadRef"
                  drag
                  action="#"
                  accept=".json"
                  :auto-upload="false"
                  :limit="1"
                  :on-change="handleJsonUpload"
                >
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">拖入 JSON 文件，或点击选择</div>
                </el-upload>

                <el-input
                  v-model="questionsStore.jsonImportText"
                  class="import-textarea"
                  type="textarea"
                  :rows="14"
                />
                <el-button type="primary" :loading="questionsStore.importing" @click="submitJsonImport">
                  执行 JSON 导入
                </el-button>
              </el-card>
            </el-col>

            <el-col :xs="24" :lg="12">
              <el-card shadow="never" class="import-card">
                <template #header>
                  <div class="card-head">
                    <strong>Excel 导入</strong>
                    <span>支持 `.xlsx` / `.xlsm` 文件，保持旧导入 API 协议。</span>
                  </div>
                </template>

                <el-form label-position="top">
                  <el-form-item label="目标单元名称">
                    <el-input v-model.trim="questionsStore.excelUnit" placeholder="例如：程序设计概述" />
                  </el-form-item>
                  <el-form-item label="选择 Excel 文件">
                    <el-upload
                      ref="excelUploadRef"
                      action="#"
                      accept=".xlsx,.xlsm"
                      :auto-upload="false"
                      :limit="1"
                      :on-change="handleExcelUpload"
                    >
                      <el-button>选择文件</el-button>
                    </el-upload>
                    <p class="import-file-hint">
                      {{ questionsStore.excelFileName ? `已选择：${questionsStore.excelFileName}` : '尚未选择文件' }}
                    </p>
                  </el-form-item>
                </el-form>

                <el-button
                  type="primary"
                  :loading="questionsStore.importing"
                  :disabled="!questionsStore.excelFile"
                  @click="submitExcelImport"
                >
                  执行 Excel 导入
                </el-button>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog
      v-model="editorVisible"
      :title="questionsStore.editingQuestionId !== null ? '编辑题目' : '新建题目'"
      width="760px"
    >
      <el-form :model="questionsStore.questionForm" label-position="top" class="question-form">
        <el-form-item label="标题">
          <el-input v-model="questionsStore.questionForm.title" placeholder="不填则自动从题干截取" />
        </el-form-item>
        <el-form-item label="题目内容">
          <el-input v-model="questionsStore.questionForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :xs="24" :md="12">
            <el-form-item label="题型">
              <el-select v-model="questionsStore.questionForm.type">
                <el-option label="选择题" value="选择题" />
                <el-option label="多选题" value="多选题" />
                <el-option label="判断题" value="判断题" />
                <el-option label="填空题" value="填空题" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="所属关卡">
              <el-select v-model="questionsStore.questionForm.level_id" filterable>
                <el-option
                  v-for="option in questionsStore.levelOptions"
                  :key="option.levelId"
                  :label="option.label"
                  :value="option.levelId"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <div v-if="questionsStore.questionForm.type === '选择题' || questionsStore.questionForm.type === '多选题'" class="option-grid">
          <el-form-item
            v-for="option in questionsStore.questionForm.options"
            :key="option.letter"
            :label="`选项 ${option.letter}`"
          >
            <el-input v-model="option.text" />
          </el-form-item>
        </div>

        <el-form-item label="正确答案">
          <el-input v-model="questionsStore.questionForm.answer" placeholder="如 A / 对 / True" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :xs="24" :md="12">
            <el-form-item label="知识点含义">
              <el-input v-model="questionsStore.questionForm.knowledge_meaning" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="知识点规则">
              <el-input v-model="questionsStore.questionForm.knowledge_rule" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="常见错误">
              <el-input v-model="questionsStore.questionForm.knowledge_error" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="示例说明">
              <el-input v-model="questionsStore.questionForm.knowledge_example" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" :loading="questionsStore.saving" @click="saveQuestion">保存题目</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="题目详情" width="680px">
      <template v-if="questionsStore.selectedQuestion">
        <div class="question-detail">
          <div>
            <h3>{{ questionsStore.selectedQuestion.title || '未命名题目' }}</h3>
            <p>{{ questionsStore.selectedQuestion.content }}</p>
          </div>
          <div v-if="questionsStore.selectedQuestion.options?.length" class="option-list">
            <article v-for="option in questionsStore.selectedQuestion.options" :key="option.letter">
              <strong>{{ option.letter }}</strong>
              <span>{{ option.text }}</span>
            </article>
          </div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="正确答案">{{ questionsStore.selectedQuestion.answer }}</el-descriptions-item>
            <el-descriptions-item label="题型">{{ questionsStore.selectedQuestion.type }}</el-descriptions-item>
            <el-descriptions-item label="单元">{{ questionsStore.selectedQuestion.unit_name }}</el-descriptions-item>
            <el-descriptions-item label="关卡">{{ questionsStore.selectedQuestion.level_name }}</el-descriptions-item>
          </el-descriptions>
          <div class="knowledge-stack">
            <p><strong>含义：</strong>{{ questionsStore.selectedQuestion.knowledge_meaning || '未填写' }}</p>
            <p><strong>规则：</strong>{{ questionsStore.selectedQuestion.knowledge_rule || '未填写' }}</p>
            <p><strong>易错点：</strong>{{ questionsStore.selectedQuestion.knowledge_error || '未填写' }}</p>
            <p><strong>示例：</strong>{{ questionsStore.selectedQuestion.knowledge_example || '未填写' }}</p>
          </div>
        </div>
      </template>
      <el-empty v-else description="请选择一题查看详情" />
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

.admin-questions-card,
.import-card {
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
}

.admin-toolbar {
  flex-wrap: wrap;
  justify-content: flex-start;
  margin-bottom: 14px;
}

.admin-toolbar .el-input {
  max-width: 300px;
}

.admin-toolbar .el-select {
  max-width: 180px;
}

.question-cell {
  display: grid;
  gap: 4px;
}

.question-cell strong {
  color: var(--admin-text);
}

.question-cell span {
  color: var(--admin-muted);
  font-size: 12px;
  line-height: 1.5;
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

.card-head strong,
.card-head span {
  display: block;
}

.card-head span {
  margin-top: 4px;
  color: var(--admin-muted);
  font-size: 13px;
}

.import-textarea {
  margin: 14px 0;
}

.import-file-hint {
  margin: 8px 0 0;
  color: var(--admin-muted);
  font-size: 13px;
}

.question-form .el-select {
  width: 100%;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 12px;
}

.question-detail {
  display: grid;
  gap: 16px;
}

.question-detail h3 {
  margin: 0 0 8px;
}

.question-detail p {
  margin: 0;
  color: #334155;
  line-height: 1.7;
}

.option-list {
  display: grid;
  gap: 8px;
}

.option-list article {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
  align-items: center;
  padding: 10px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
}

.option-list strong {
  display: inline-grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 999px;
  background: var(--admin-primary-soft);
  color: var(--admin-primary);
}

.knowledge-stack {
  display: grid;
  gap: 8px;
}

@media (max-width: 760px) {
  .admin-page__heading,
  .admin-table-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .option-grid {
    grid-template-columns: 1fr;
  }
}
</style>
