<template>
  <view class="plan-create-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">{{ isEdit ? '编辑计划' : '创建计划' }}</text>
      <view class="nav-right">
        <text v-if="isEdit" class="delete-btn" @click="handleDelete">删除</text>
      </view>
    </view>

    <!-- 表单内容 -->
    <view class="form-container">
      <!-- 标题输入 -->
      <view class="form-section">
        <text class="section-label">计划标题</text>
        <view class="input-wrapper">
          <input
            v-model="title"
            class="title-input"
            placeholder="输入计划标题..."
            maxlength="256"
            :focus="!isEdit"
          />
          <text class="char-count">{{ title.length }}/256</text>
        </view>
      </view>

      <!-- 时间范围 -->
      <view class="form-section">
        <text class="section-label">时间范围</text>
        <view class="date-row">
          <view class="date-picker" @click="showStartPicker = true">
            <text class="date-label">开始日期</text>
            <text class="date-value">{{ startDate || '请选择' }}</text>
          </view>
          <text class="date-separator">~</text>
          <view class="date-picker" @click="showEndPicker = true">
            <text class="date-label">结束日期</text>
            <text class="date-value">{{ endDate || '请选择' }}</text>
          </view>
        </view>
      </view>

      <!-- 负责人选择 -->
      <view class="form-section">
        <text class="section-label">负责人</text>
        <view class="owner-selector" @click="showOwnerPicker = true">
          <text v-if="selectedOwnerName" class="owner-selected">{{ selectedOwnerName }}</text>
          <text v-else class="owner-placeholder">选择负责人...</text>
          <text class="owner-arrow">›</text>
        </view>
        <text class="section-hint">负责人必须是当前家庭成员</text>
      </view>

      <!-- 关联目标选择 -->
      <view class="form-section">
        <text class="section-label">关联目标（可选）</text>
        <view class="goal-selector" @click="showGoalPicker = true">
          <text v-if="selectedGoal" class="goal-selected">{{ selectedGoal.title }}</text>
          <text v-else class="goal-placeholder">选择关联的目标...</text>
          <text class="goal-arrow">›</text>
        </view>
        <view v-if="selectedGoal" class="goal-clear" @click="clearGoal">
          <text class="clear-text">取消关联</text>
        </view>
      </view>

      <!-- 步骤管理（编辑模式） -->
      <view v-if="isEdit && currentPlan" class="form-section">
        <view class="section-header">
          <text class="section-label">实现步骤</text>
          <view class="add-step-btn" @click="showAddStep = true">
            <text class="add-step-text">+ 添加步骤</text>
          </view>
        </view>

        <view v-if="currentPlan.steps.length === 0" class="steps-empty">
          <text class="steps-empty-text">暂无步骤，点击上方添加</text>
        </view>

        <view v-else class="steps-list">
          <view
            v-for="(step, index) in currentPlan.steps"
            :key="step.id"
            class="step-item"
          >
            <view class="step-left">
              <view class="step-number">{{ index + 1 }}</view>
              <view class="step-info">
                <text class="step-title">{{ step.title }}</text>
                <view class="step-badges">
                  <text class="step-type-badge" :class="step.step_type">
                    {{ step.step_type === 'task' ? '任务' : '行动' }}
                  </text>
                  <text v-if="step.is_bounty" class="bounty-badge">🏆 悬赏</text>
                </view>
              </view>
            </view>
            <view class="step-actions">
              <text class="step-status" :class="step.status">
                {{ stepStatusLabel(step.status) }}
              </text>
              <text class="step-delete" @click.stop="handleDeleteStep(step.id)">✕</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 日期选择器 - 开始日期 -->
    <view v-if="showStartPicker" class="picker-mask" @click="showStartPicker = false">
      <view class="picker-container" @click.stop>
        <view class="picker-header">
          <text class="picker-cancel" @click="showStartPicker = false">取消</text>
          <text class="picker-title">选择开始日期</text>
          <text class="picker-confirm" @click="confirmStartDate">确定</text>
        </view>
        <picker-view
          class="date-picker-view"
          :value="startPickerValue"
          @change="onStartPickerChange"
        >
          <picker-view-column>
            <view v-for="year in years" :key="year" class="picker-item">{{ year }}年</view>
          </picker-view-column>
          <picker-view-column>
            <view v-for="month in 12" :key="month" class="picker-item">{{ month }}月</view>
          </picker-view-column>
          <picker-view-column>
            <view v-for="day in 31" :key="day" class="picker-item">{{ day }}日</view>
          </picker-view-column>
        </picker-view>
      </view>
    </view>

    <!-- 日期选择器 - 结束日期 -->
    <view v-if="showEndPicker" class="picker-mask" @click="showEndPicker = false">
      <view class="picker-container" @click.stop>
        <view class="picker-header">
          <text class="picker-cancel" @click="showEndPicker = false">取消</text>
          <text class="picker-title">选择结束日期</text>
          <text class="picker-confirm" @click="confirmEndDate">确定</text>
        </view>
        <picker-view
          class="date-picker-view"
          :value="endPickerValue"
          @change="onEndPickerChange"
        >
          <picker-view-column>
            <view v-for="year in years" :key="year" class="picker-item">{{ year }}年</view>
          </picker-view-column>
          <picker-view-column>
            <view v-for="month in 12" :key="month" class="picker-item">{{ month }}月</view>
          </picker-view-column>
          <picker-view-column>
            <view v-for="day in 31" :key="day" class="picker-item">{{ day }}日</view>
          </picker-view-column>
        </picker-view>
      </view>
    </view>

    <!-- 负责人选择弹窗 -->
    <view v-if="showOwnerPicker" class="picker-mask" @click="showOwnerPicker = false">
      <view class="list-picker-container" @click.stop>
        <view class="picker-header">
          <text class="picker-title">选择负责人</text>
          <text class="picker-close" @click="showOwnerPicker = false">✕</text>
        </view>
        <scroll-view class="picker-list" scroll-y>
          <view v-if="familyMembers.length === 0" class="picker-empty">
            <text>暂无家庭成员</text>
          </view>
          <view
            v-for="member in familyMembers"
            :key="member.id"
            class="picker-item-row"
            :class="{ selected: ownerId === member.user_id }"
            @click="selectOwner(member)"
          >
            <text class="picker-item-title">{{ member.nickname || '家庭成员' }}</text>
            <text v-if="ownerId === member.user_id" class="picker-check">✓</text>
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- 目标选择弹窗 -->
    <view v-if="showGoalPicker" class="picker-mask" @click="showGoalPicker = false">
      <view class="list-picker-container" @click.stop>
        <view class="picker-header">
          <text class="picker-title">选择关联目标</text>
          <text class="picker-close" @click="showGoalPicker = false">✕</text>
        </view>
        <scroll-view class="picker-list" scroll-y>
          <view v-if="goals.length === 0" class="picker-empty">
            <text>暂无目标，请先创建目标</text>
          </view>
          <view
            v-for="goal in goals"
            :key="goal.id"
            class="picker-item-row"
            :class="{ selected: selectedGoal?.id === goal.id }"
            @click="selectGoal(goal)"
          >
            <text class="picker-item-title">{{ goal.title }}</text>
            <text v-if="selectedGoal?.id === goal.id" class="picker-check">✓</text>
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- 添加步骤弹窗 -->
    <view v-if="showAddStep" class="picker-mask" @click="showAddStep = false">
      <view class="list-picker-container" @click.stop>
        <view class="picker-header">
          <text class="picker-title">添加步骤</text>
          <text class="picker-close" @click="showAddStep = false">✕</text>
        </view>
        <view class="step-form">
          <view class="step-form-field">
            <text class="step-form-label">步骤标题</text>
            <input
              v-model="newStepTitle"
              class="step-form-input"
              placeholder="输入步骤标题..."
              maxlength="256"
            />
          </view>
          <view class="step-form-field">
            <text class="step-form-label">步骤类型</text>
            <view class="type-options">
              <view
                class="type-option"
                :class="{ active: newStepType === 'task' }"
                @click="newStepType = 'task'"
              >
                <text>任务</text>
              </view>
              <view
                class="type-option"
                :class="{ active: newStepType === 'action' }"
                @click="newStepType = 'action'"
              >
                <text>行动</text>
              </view>
            </view>
          </view>
          <view class="step-form-field">
            <view class="bounty-toggle" @click="newStepBounty = !newStepBounty">
              <text class="bounty-label">设为悬赏任务</text>
              <view class="toggle" :class="{ on: newStepBounty }">
                <view class="toggle-dot"></view>
              </view>
            </view>
          </view>
          <view
            class="step-submit-btn"
            :class="{ disabled: !newStepTitle.trim() }"
            @click="handleAddStep"
          >
            <text class="step-submit-text">添加</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部操作栏 -->
    <view class="bottom-bar">
      <view
        class="submit-btn"
        :class="{ disabled: !canSubmit || submitting }"
        @click="handleSubmit"
      >
        <text class="submit-text">
          {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '创建计划') }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { usePlanStore } from '@/stores/plan'
import { goalApi } from '@/services/api/goals'
import type { GoalItem, PlanItem, StepType, PlanStepStatus } from '@/services/types'

const planStore = usePlanStore()

// Page state
const title = ref('')
const startDate = ref('')
const endDate = ref('')
const ownerId = ref('')
const selectedOwnerName = ref('')
const isEdit = ref(false)
const planId = ref('')
const currentPlan = ref<PlanItem | null>(null)
const submitting = ref(false)

// Goal selection
const goals = ref<GoalItem[]>([])
const selectedGoal = ref<GoalItem | null>(null)
const showGoalPicker = ref(false)

// Owner selection
interface FamilyMemberInfo {
  id: string
  user_id: string
  nickname: string
}
const familyMembers = ref<FamilyMemberInfo[]>([])
const showOwnerPicker = ref(false)

// Date pickers
const showStartPicker = ref(false)
const showEndPicker = ref(false)
const startPickerValue = ref([0, 0, 0])
const endPickerValue = ref([0, 0, 0])
const currentYear = new Date().getFullYear()
const years = Array.from({ length: 10 }, (_, i) => currentYear + i)

// Step form
const showAddStep = ref(false)
const newStepTitle = ref('')
const newStepType = ref<StepType>('task')
const newStepBounty = ref(false)

// Computed
const canSubmit = computed(() => title.value.trim().length > 0 && ownerId.value.length > 0)

// Page load
onLoad((query) => {
  const id = query?.id
  if (id) {
    isEdit.value = true
    planId.value = id
    loadPlan(id)
  }
})

onMounted(() => {
  loadGoals()
  loadFamilyMembers()
})

/** Load goals for selection */
async function loadGoals(): Promise<void> {
  try {
    const res = await goalApi.getGoals({ page: 1, page_size: 100, status: 'active' })
    goals.value = res.items
  } catch {
    // Silent fail - goal selection is optional
  }
}

/** Load family members for owner selection */
async function loadFamilyMembers(): Promise<void> {
  // For now, use current user as default. Full member list requires families API.
  // This will be populated from the user store / families API
  try {
    const userInfo = uni.getStorageSync('userInfo')
    if (userInfo) {
      const user = typeof userInfo === 'string' ? JSON.parse(userInfo) : userInfo
      familyMembers.value = [{
        id: user.id,
        user_id: user.id,
        nickname: user.nickname || '我',
      }]
      // Default owner to current user
      if (!ownerId.value) {
        ownerId.value = user.id
        selectedOwnerName.value = user.nickname || '我'
      }
    }
  } catch {
    // Silent fail
  }
}

/** Load plan details */
async function loadPlan(id: string): Promise<void> {
  try {
    const plan = await planStore.fetchPlan(id)
    currentPlan.value = plan
    title.value = plan.title
    startDate.value = plan.start_date || ''
    endDate.value = plan.end_date || ''
    ownerId.value = plan.owner_id
    if (plan.goal_id) {
      const goal = goals.value.find(g => g.id === plan.goal_id)
      if (goal) selectedGoal.value = goal
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
    setTimeout(() => goBack(), 1500)
  }
}

// Date picker handlers
function onStartPickerChange(e: { detail: { value: number[] } }): void {
  startPickerValue.value = e.detail.value
}

function onEndPickerChange(e: { detail: { value: number[] } }): void {
  endPickerValue.value = e.detail.value
}

function confirmStartDate(): void {
  const [yi, mi, di] = startPickerValue.value
  const year = years[yi] || currentYear
  const month = String(mi + 1).padStart(2, '0')
  const day = String(di + 1).padStart(2, '0')
  startDate.value = `${year}-${month}-${day}`
  showStartPicker.value = false
}

function confirmEndDate(): void {
  const [yi, mi, di] = endPickerValue.value
  const year = years[yi] || currentYear
  const month = String(mi + 1).padStart(2, '0')
  const day = String(di + 1).padStart(2, '0')
  endDate.value = `${year}-${month}-${day}`
  showEndPicker.value = false
}

// Owner selection
function selectOwner(member: FamilyMemberInfo): void {
  ownerId.value = member.user_id
  selectedOwnerName.value = member.nickname
  showOwnerPicker.value = false
}

// Goal selection
function selectGoal(goal: GoalItem): void {
  selectedGoal.value = goal
  showGoalPicker.value = false
}

function clearGoal(): void {
  selectedGoal.value = null
}

// Step management
function stepStatusLabel(status: PlanStepStatus): string {
  const map: Record<PlanStepStatus, string> = {
    pending: '待开始',
    in_progress: '进行中',
    completed: '已完成',
  }
  return map[status] || status
}

async function handleAddStep(): Promise<void> {
  if (!newStepTitle.value.trim() || !currentPlan.value) return

  try {
    await planStore.addStep(currentPlan.value.id, {
      title: newStepTitle.value.trim(),
      step_type: newStepType.value,
      is_bounty: newStepBounty.value,
      sort_order: currentPlan.value.steps.length,
    })
    // Reset form
    newStepTitle.value = ''
    newStepType.value = 'task'
    newStepBounty.value = false
    showAddStep.value = false
    uni.showToast({ title: '步骤已添加', icon: 'success' })
  } catch {
    uni.showToast({ title: '添加失败', icon: 'none' })
  }
}

async function handleDeleteStep(stepId: string): Promise<void> {
  if (!currentPlan.value) return

  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个步骤吗？',
    confirmColor: '#ff4444',
    success: async (res) => {
      if (res.confirm && currentPlan.value) {
        try {
          await planStore.deleteStep(currentPlan.value.id, stepId)
          uni.showToast({ title: '已删除', icon: 'success' })
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
}

// Form submission
async function handleSubmit(): Promise<void> {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    if (isEdit.value) {
      const plan = await planStore.updatePlan(planId.value, {
        title: title.value.trim(),
        start_date: startDate.value || undefined,
        end_date: endDate.value || undefined,
        owner_id: ownerId.value,
      })
      currentPlan.value = plan
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      const plan = await planStore.createPlan({
        title: title.value.trim(),
        goal_id: selectedGoal.value?.id,
        start_date: startDate.value || undefined,
        end_date: endDate.value || undefined,
        owner_id: ownerId.value,
      })
      uni.showToast({ title: '创建成功', icon: 'success' })
      setTimeout(() => {
        uni.redirectTo({ url: `/pages/plans/create?id=${plan.id}` })
      }, 1000)
    }
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

// Delete plan
async function handleDelete(): Promise<void> {
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，确定要删除这个计划吗？',
    confirmColor: '#ff4444',
    success: async (res) => {
      if (res.confirm) {
        try {
          await planStore.deletePlan(planId.value)
          uni.showToast({ title: '已删除', icon: 'success' })
          setTimeout(() => goBack(), 1000)
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
}

function goBack(): void {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.plan-create-page {
  min-height: 100vh;
  background-color: #f5f6fa;
  padding-bottom: 140rpx;
}

// 导航栏
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}

.nav-back {
  padding: 12rpx;
}

.back-icon {
  font-size: 36rpx;
  color: #333;
}

.nav-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a1a2e;
}

.nav-right {
  min-width: 80rpx;
  text-align: right;
}

.delete-btn {
  font-size: 28rpx;
  color: #ff4444;
}

// 表单
.form-container {
  padding: 32rpx;
}

.form-section {
  margin-bottom: 40rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.section-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
  display: block;
}

.section-hint {
  font-size: 24rpx;
  color: #999;
  margin-top: 12rpx;
  display: block;
}

.input-wrapper {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.title-input {
  width: 100%;
  font-size: 32rpx;
  color: #333;
  margin-bottom: 8rpx;
}

.char-count {
  font-size: 22rpx;
  color: #ccc;
  text-align: right;
  display: block;
}

// 日期选择
.date-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.date-picker {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.date-label {
  font-size: 22rpx;
  color: #999;
  display: block;
  margin-bottom: 8rpx;
}

.date-value {
  font-size: 28rpx;
  color: #333;
}

.date-separator {
  font-size: 28rpx;
  color: #999;
}

// 负责人/目标选择器
.owner-selector,
.goal-selector {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.owner-selected,
.goal-selected {
  font-size: 28rpx;
  color: #333;
}

.owner-placeholder,
.goal-placeholder {
  font-size: 28rpx;
  color: #ccc;
}

.owner-arrow,
.goal-arrow {
  font-size: 36rpx;
  color: #ccc;
}

.goal-clear {
  margin-top: 12rpx;
}

.clear-text {
  font-size: 24rpx;
  color: #ff4444;
}

// 步骤管理
.add-step-btn {
  padding: 8rpx 20rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20rpx;
}

.add-step-text {
  font-size: 24rpx;
  color: #fff;
}

.steps-empty {
  background: #fff;
  border-radius: 16rpx;
  padding: 48rpx;
  text-align: center;
}

.steps-empty-text {
  font-size: 26rpx;
  color: #999;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.step-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.step-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
  flex: 1;
}

.step-number {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 22rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-info {
  flex: 1;
}

.step-title {
  font-size: 26rpx;
  color: #333;
  display: block;
  margin-bottom: 6rpx;
}

.step-badges {
  display: flex;
  gap: 8rpx;
}

.step-type-badge {
  font-size: 20rpx;
  padding: 2rpx 12rpx;
  border-radius: 8rpx;

  &.task {
    background: #e3f2fd;
    color: #1565c0;
  }

  &.action {
    background: #e8f5e9;
    color: #2e7d32;
  }
}

.bounty-badge {
  font-size: 20rpx;
  padding: 2rpx 12rpx;
  border-radius: 8rpx;
  background: #fff3e0;
  color: #e65100;
}

.step-actions {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.step-status {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;

  &.pending {
    background: #f5f5f5;
    color: #9e9e9e;
  }

  &.in_progress {
    background: #e8f5e9;
    color: #2e7d32;
  }

  &.completed {
    background: #e3f2fd;
    color: #1565c0;
  }
}

.step-delete {
  font-size: 28rpx;
  color: #ccc;
  padding: 8rpx;
}

// 弹窗通用
.picker-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: flex-end;
}

.picker-container {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 32rpx;
}

.list-picker-container {
  width: 100%;
  max-height: 70vh;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 32rpx;
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.picker-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.picker-cancel {
  font-size: 28rpx;
  color: #999;
}

.picker-confirm {
  font-size: 28rpx;
  color: #667eea;
  font-weight: 600;
}

.picker-close {
  font-size: 32rpx;
  color: #999;
  padding: 8rpx;
}

.date-picker-view {
  height: 400rpx;
}

.picker-item {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
}

.picker-list {
  max-height: 50vh;
}

.picker-empty {
  padding: 48rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
}

.picker-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 16rpx;
  border-bottom: 1rpx solid #f5f5f5;

  &.selected {
    background: #f0f4ff;
  }
}

.picker-item-title {
  font-size: 28rpx;
  color: #333;
}

.picker-check {
  font-size: 28rpx;
  color: #667eea;
  font-weight: 700;
}

// 步骤表单
.step-form {
  padding: 16rpx 0;
}

.step-form-field {
  margin-bottom: 24rpx;
}

.step-form-label {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 12rpx;
  display: block;
}

.step-form-input {
  width: 100%;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
}

.type-options {
  display: flex;
  gap: 16rpx;
}

.type-option {
  flex: 1;
  padding: 16rpx;
  text-align: center;
  border-radius: 12rpx;
  background: #f5f6fa;
  font-size: 28rpx;
  color: #666;

  &.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
  }
}

.bounty-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 0;
}

.bounty-label {
  font-size: 28rpx;
  color: #333;
}

.toggle {
  width: 80rpx;
  height: 44rpx;
  border-radius: 22rpx;
  background: #e0e0e0;
  position: relative;
  transition: background 0.3s;

  &.on {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
}

.toggle-dot {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  transition: transform 0.3s;

  .on & {
    transform: translateX(36rpx);
  }
}

.step-submit-btn {
  width: 100%;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 40rpx;
  margin-top: 24rpx;

  &.disabled {
    opacity: 0.5;
  }
}

.step-submit-text {
  font-size: 28rpx;
  color: #fff;
  font-weight: 600;
}

// 底部操作栏
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.4);

  &.disabled {
    opacity: 0.5;
    box-shadow: none;
  }
}

.submit-text {
  font-size: 30rpx;
  color: #fff;
  font-weight: 600;
}
</style>
