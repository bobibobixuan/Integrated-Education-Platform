<script setup lang="ts">
import { onMounted } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { useAdminAnalyticsStore } from '@/stores/adminAnalytics'
import type { AdminLevelAnalyticsItem, AdminWrongQuestionItem } from '@/types/api'

const analyticsStore = useAdminAnalyticsStore()

function selectLevel(row: AdminLevelAnalyticsItem) {
  analyticsStore.selectedLevelKey = `${row.unit_name}-${row.level_name}`
}

function selectWrongQuestion(row: AdminWrongQuestionItem) {
  analyticsStore.selectedWrongQuestionId = row.question_id
}

onMounted(() => {
  void analyticsStore.refreshAll()
})
</script>

<template>
  <section class="admin-page">
    <div class="admin-page__heading">
      <div>
        <p>Analytics</p>
        <h2>教学分析</h2>
      </div>
      <el-button :icon="Refresh" :loading="analyticsStore.loading || analyticsStore.wrongLoading" @click="analyticsStore.refreshAll">
        刷新分析
      </el-button>
    </div>

    <el-alert
      v-if="analyticsStore.error"
      class="admin-page__alert"
      :title="analyticsStore.error"
      type="error"
      show-icon
      :closable="false"
    />

    <el-card shadow="never" class="admin-analytics-card">
      <el-tabs v-model="analyticsStore.activeTab">
        <el-tab-pane label="单元分析" name="units">
          <el-skeleton v-if="analyticsStore.loading && analyticsStore.levelAnalytics.length === 0" :rows="10" animated />
          <template v-else>
            <el-row :gutter="16">
              <el-col v-for="item in analyticsStore.analyticsKpis" :key="item.label" :xs="24" :sm="12" :lg="6">
                <el-card shadow="never" class="analytics-kpi-card">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.hint }}</small>
                </el-card>
              </el-col>
            </el-row>

            <el-row :gutter="16" class="analytics-section">
              <el-col :xs="24" :lg="12">
                <el-card shadow="never" class="analytics-subcard">
                  <template #header>低正确率单元提示</template>
                  <el-empty v-if="analyticsStore.riskUnits.length === 0" description="暂无风险单元数据" />
                  <div v-else class="risk-list">
                    <article v-for="unit in analyticsStore.riskUnits" :key="unit.unitName">
                      <div>
                        <strong>{{ unit.unitName }}</strong>
                        <span>{{ analyticsStore.formatNumber(unit.attempts) }} 次作答 · {{ unit.levelCount }} 个关卡</span>
                      </div>
                      <el-tag :type="unit.avgAccuracy < 60 ? 'danger' : 'warning'">
                        {{ analyticsStore.formatPercent(unit.avgAccuracy) }}
                      </el-tag>
                    </article>
                  </div>
                </el-card>
              </el-col>
              <el-col :xs="24" :lg="12">
                <el-card shadow="never" class="analytics-subcard">
                  <template #header>单元聚合明细</template>
                  <el-table :data="analyticsStore.unitSummaryRows" border height="260">
                    <el-table-column prop="unitName" label="单元" min-width="140" />
                    <el-table-column label="正确率" width="110">
                      <template #default="{ row }">{{ analyticsStore.formatPercent(row.avgAccuracy) }}</template>
                    </el-table-column>
                    <el-table-column label="平均耗时" width="110">
                      <template #default="{ row }">{{ analyticsStore.formatSeconds(row.avgTime) }}</template>
                    </el-table-column>
                    <el-table-column label="答题量" width="100">
                      <template #default="{ row }">{{ analyticsStore.formatNumber(row.attempts) }}</template>
                    </el-table-column>
                  </el-table>
                </el-card>
              </el-col>
            </el-row>

            <el-card shadow="never" class="analytics-subcard">
              <template #header>
                <div class="analytics-card-head">
                  <strong>关卡明细</strong>
                  <el-select v-model="analyticsStore.selectedUnitName" clearable placeholder="全部单元">
                    <el-option v-for="unit in analyticsStore.units" :key="unit.id" :label="unit.name" :value="unit.name" />
                  </el-select>
                </div>
              </template>
              <el-table
                :data="analyticsStore.filteredLevelAnalytics"
                border
                empty-text="暂无关卡分析数据"
                @row-click="selectLevel"
              >
                <el-table-column prop="unit_name" label="单元" min-width="140" />
                <el-table-column prop="level_name" label="关卡" min-width="140" />
                <el-table-column label="参与人数" width="110">
                  <template #default="{ row }">{{ analyticsStore.formatNumber(row.student_count) }}</template>
                </el-table-column>
                <el-table-column label="作答次数" width="110">
                  <template #default="{ row }">{{ analyticsStore.formatNumber(row.total_attempts) }}</template>
                </el-table-column>
                <el-table-column label="正确率" width="110">
                  <template #default="{ row }">{{ analyticsStore.formatPercent(row.correct_rate) }}</template>
                </el-table-column>
                <el-table-column label="平均耗时" width="110">
                  <template #default="{ row }">{{ analyticsStore.formatSeconds(row.avg_time_spent) }}</template>
                </el-table-column>
              </el-table>
            </el-card>

            <el-card v-if="analyticsStore.selectedLevelAnalytics" shadow="never" class="analytics-subcard">
              <template #header>当前关卡焦点</template>
              <el-row :gutter="12">
                <el-col :xs="24" :sm="12" :lg="6">
                  <div class="focus-metric"><span>单元</span><strong>{{ analyticsStore.selectedLevelAnalytics.unit_name }}</strong></div>
                </el-col>
                <el-col :xs="24" :sm="12" :lg="6">
                  <div class="focus-metric"><span>关卡</span><strong>{{ analyticsStore.selectedLevelAnalytics.level_name }}</strong></div>
                </el-col>
                <el-col :xs="24" :sm="12" :lg="6">
                  <div class="focus-metric"><span>正确率</span><strong>{{ analyticsStore.formatPercent(analyticsStore.selectedLevelAnalytics.correct_rate) }}</strong></div>
                </el-col>
                <el-col :xs="24" :sm="12" :lg="6">
                  <div class="focus-metric"><span>平均耗时</span><strong>{{ analyticsStore.formatSeconds(analyticsStore.selectedLevelAnalytics.avg_time_spent) }}</strong></div>
                </el-col>
              </el-row>
            </el-card>
          </template>
        </el-tab-pane>

        <el-tab-pane label="错题统计" name="wrong">
          <el-skeleton v-if="analyticsStore.wrongLoading && analyticsStore.wrongQuestionStats.length === 0" :rows="8" animated />
          <template v-else>
            <el-row :gutter="16">
              <el-col v-for="item in analyticsStore.wrongKpis" :key="item.label" :xs="24" :sm="8">
                <el-card shadow="never" class="analytics-kpi-card">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.hint }}</small>
                </el-card>
              </el-col>
            </el-row>

            <el-card shadow="never" class="analytics-subcard analytics-section">
              <template #header>高频错题</template>
              <el-empty v-if="analyticsStore.highFrequencyWrongQuestions.length === 0" description="暂无错题统计数据" />
              <div v-else class="wrong-highlight-list">
                <article v-for="row in analyticsStore.highFrequencyWrongQuestions" :key="row.question_id">
                  <div>
                    <strong>{{ row.unit_name }} / {{ row.level_name }}</strong>
                    <p>{{ row.question_content }}</p>
                  </div>
                  <el-tag type="danger">{{ analyticsStore.formatNumber(row.wrong_count) }} 次</el-tag>
                </article>
              </div>
            </el-card>

            <el-card shadow="never" class="analytics-subcard">
              <template #header>
                <div class="analytics-card-head">
                  <strong>错题明细</strong>
                  <el-input
                    v-model.trim="analyticsStore.wrongKeyword"
                    :prefix-icon="Search"
                    clearable
                    placeholder="搜索题目 / 单元 / 关卡"
                  />
                </div>
              </template>
              <el-table
                :data="analyticsStore.filteredWrongQuestionStats"
                border
                empty-text="暂无错题统计数据"
                @row-click="selectWrongQuestion"
              >
                <el-table-column prop="question_content" label="题目内容" min-width="260" />
                <el-table-column prop="unit_name" label="单元" min-width="130" />
                <el-table-column prop="level_name" label="关卡" min-width="130" />
                <el-table-column label="错误次数" width="110">
                  <template #default="{ row }">{{ analyticsStore.formatNumber(row.wrong_count) }}</template>
                </el-table-column>
                <el-table-column label="错误率" width="110">
                  <template #default="{ row }">{{ analyticsStore.formatPercent(row.wrong_rate) }}</template>
                </el-table-column>
                <el-table-column label="总作答" width="110">
                  <template #default="{ row }">{{ analyticsStore.formatNumber(row.total_attempts) }}</template>
                </el-table-column>
              </el-table>
            </el-card>

            <el-card v-if="analyticsStore.selectedWrongQuestion" shadow="never" class="analytics-subcard">
              <template #header>当前错题</template>
              <p class="question-preview">{{ analyticsStore.selectedWrongQuestion.question_content }}</p>
              <el-row :gutter="12">
                <el-col :xs="24" :sm="8">
                  <div class="focus-metric"><span>错误次数</span><strong>{{ analyticsStore.formatNumber(analyticsStore.selectedWrongQuestion.wrong_count) }}</strong></div>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <div class="focus-metric"><span>错误率</span><strong>{{ analyticsStore.formatPercent(analyticsStore.selectedWrongQuestion.wrong_rate) }}</strong></div>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <div class="focus-metric"><span>总作答</span><strong>{{ analyticsStore.formatNumber(analyticsStore.selectedWrongQuestion.total_attempts) }}</strong></div>
                </el-col>
              </el-row>
            </el-card>
          </template>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </section>
</template>

<style scoped>
.admin-page__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
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

.admin-analytics-card,
.analytics-kpi-card,
.analytics-subcard {
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
}

.analytics-kpi-card {
  min-height: 118px;
  margin-bottom: 16px;
}

.analytics-kpi-card span,
.analytics-kpi-card small {
  display: block;
  color: var(--admin-muted);
}

.analytics-kpi-card strong {
  display: block;
  margin: 10px 0;
  color: var(--admin-text);
  font-size: 28px;
  line-height: 1;
}

.analytics-section,
.analytics-subcard {
  margin-top: 16px;
}

.analytics-card-head {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.analytics-card-head .el-select,
.analytics-card-head .el-input {
  max-width: 280px;
}

.risk-list,
.wrong-highlight-list {
  display: grid;
  gap: 10px;
}

.risk-list article,
.wrong-highlight-list article {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
}

.risk-list strong,
.risk-list span,
.wrong-highlight-list strong,
.wrong-highlight-list p {
  display: block;
}

.risk-list span,
.wrong-highlight-list p {
  margin: 4px 0 0;
  color: var(--admin-muted);
  font-size: 13px;
  line-height: 1.5;
}

.focus-metric {
  display: grid;
  gap: 6px;
  min-height: 82px;
  padding: 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
}

.focus-metric span {
  color: var(--admin-muted);
  font-size: 12px;
}

.focus-metric strong {
  color: var(--admin-text);
  font-size: 18px;
}

.question-preview {
  margin: 0 0 14px;
  color: #334155;
  line-height: 1.7;
}

@media (max-width: 760px) {
  .admin-page__heading,
  .analytics-card-head,
  .risk-list article,
  .wrong-highlight-list article {
    align-items: flex-start;
    flex-direction: column;
  }

  .analytics-card-head .el-select,
  .analytics-card-head .el-input {
    max-width: none;
    width: 100%;
  }
}
</style>
