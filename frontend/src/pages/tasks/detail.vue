<template>
  <view class="task-detail-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">任务详情</text>
      <view class="nav-right">
        <text v-if="canEdit" class="edit-btn" @click="goEdit">编辑</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 任务内容 -->
    <scroll-view v-else-if="task" class="detail-content" scroll-y>
      <!-- 封面图 -->
      <image
        v-if="task.cover_image_url"
        :src="task.cover_image_url"
        class="cover-image"
        mode="aspectFill"
      />

      <!-- 基本信息 -->
      <view class="info-section">
        <text class="task-title">{{ task.title }}</text>
        <view class="status-row">
          <view class="status-badge" :class="'status-' + task.status">
            {{ statusLabel(task.status) }}
          </view>
          <view class="type-badge">
            {{ task.task_type === 'once' ? '📋 单次' : '🔄 重复' }}
          </view>
        </view>
        <text v-if="task.display_text" class="display-text">{{ task.display_text }}</text>
        <text v-if="task.description" class="description">{{ task.description }}</text>
      </view>

      <!-- 积分信息 -->
      <view class="section" v-if="task.reward_points || task.penalty_points">
        <text class="section-title">积分设置</text>
        <view class="points-info">
          <view v-if="task.reward_points" class="points-item reward">
            <text class="points-icon">🎁</text>
            <text class="points-text">完成奖励 +{{ task.reward_points }} 分</text>
          </view>
          <view v-if="task.penalty_points" class="points-item penalty">
            <text class="points-icon">⚠️</text>
            <text class="points-text">超时惩罚 -{{ task.penalty_points }} 分</text>
          </view>
        </view>
      </view>

      <!-- 时间信息 -->
      <view class="section">
        <text class="section-title">时间信息</text>
        <view class="info-list">
          <view v-if="task.time_limit_hours" class="info-row">
            <text class="info-label">时限</text>
            <text class="info-value">{{ task.time_limit_hours }} 小时</text>
          </view>
          <view v-if="task.deadline_at" class="info-row">
            <text class="info-label">截止时间</text>
            <text class="info-value">{{ formatDate(task.deadline_at) }}</text>
          </view>
          <!-- 倒计时 -->
          <view v-if="task.deadline_at && countdownText" class="info-row">
            <text class="info-label">剩余时间</text>
            <text class="info-value" :class="{ 'countdown-urgent': isUrgent }">{{ countdownText }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">创建时间</text>
            <text class="info-value">{{ formatDate(task.created_at) }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">更新时间</text>
            <text class="info-value">{{ formatDate(task.updated_at) }}</text>
          </view>
        </view>
      </view>

      <!-- 审核状态 -->
      <view class="section" v-if="task.status === 'submitted' || task.status === 'approved' || task.status === 'rejected'">
        <text class="section-title">审核状态</text>
        <view class="review-status-card" :class="'review-' + task.status">
          <text class="review-icon">{{ task.status === 'approved' ? '✅' : task.status === 'rejected' ? '❌' : '⏳' }}</text>
          <view class="review-info">
            <text class="review-label">{{ reviewStatusLabel(task.status) }}</text>
            <text class="review-hint">{{ reviewHint(task.status) }}</text>
          </view>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom"></view>
    </scroll-view>

    <!-- 底部操作栏 -->
    <view v-if="task" class="action-bar">
      <button
        v-if="canSubmit"
        class="action-btn primary"
        @click="goSubmit"
      >
        提交完成
      </button>
      <button
        v-if="canEdit"
        class="action-btn secondary"
        @click="goEdit"
      >
        编辑任务
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { taskApi } from '@/services/api/tasks'
import type { TaskItem } from '@/services/types'

const task = ref<TaskItem | null>(null)
const loading = ref(true)
const countdownText = ref('')
const isUrgent = ref(false)
let taskId = ''
let countdownTimer: ReturnType<typeof setInterval> | null = null

const canEdit = computed(() => {
  if (!task.value) return false
  return ['pending', 'claimed', 'in_progress', 'rejected'].includes(task.value.status)
})

const canSubmit = computed(() => {
  if (!task.value) return false
  return ['claimed', 'in_progress', 'rejected'].includes(task.value.status)
})

function startCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  updateCountdown()
  countdownTimer = setInterval(updateCountdown, 1000)
}

function updateCountdown() {
  if (!task.value?.deadline_at) {
    countdownText.value = ''
    return
  }
  const deadline = new Date(task.value.deadline_at).getTime()
  const now = Date.now()
  const diff = deadline - now

  if (diff <= 0) {
    countdownText.value = '已超时'
    isUrgent.value = true
    if (countdownTimer) clearInterval(countdownTimer)
    return
  }

  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  countdownText.value = `${hours}时${String(minutes).padStart(2, '0')}分${String(seconds).padStart(2, '0')}秒`
  isUrgent.value = hours < 2
}

function reviewStatusLabel(status: string): string {
  const map: Record<string, string> = {
    submitted: '等待审核',
    approved: '审核通过',
    rejected: '审核驳回',
  }
  return map[status] || status
}

function reviewHint(status: string): string {
  const map: Record<string, string> = {
    submitted: '已提交，等待家长审核',
    approved: '任务已完成，积分已发放',
    rejected: '审核未通过，可重新提交',
  }
  return map[status] || ''
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})

onLoad((query) => {
  const id = query?.id
  if (id) {
    taskId = id
    loadTask(id)
  }
})

async function loadTask(id: string) {
  loading.value = true
  try {
    task.value = await taskApi.getTask(id)
    if (task.value?.deadline_at) {
      startCountdown()
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function goBack() {
  uni.navigateBack()
}

function goEdit() {
  uni.navigateTo({ url: `/pages/tasks/create?id=${taskId}` })
}

function goSubmit() {
  uni.navigateTo({ url: `/pages/tasks/submit?id=${taskId}` })
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待认领',
    claimed: '已认领',
    in_progress: '进行中',
    submitted: '待审核',
    approved: '已完成',
    rejected: '已驳回',
    expired: '已超时',
  }
  return map[status] || status
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.task-detail-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f6fa;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 88rpx 32rpx 24rpx;
  background: #fff;
}

.nav-back {
  width: 64rpx;
}

.back-icon {
  font-size: 36rpx;
  color: #333;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.nav-right {
  width: 64rpx;
  display: flex;
  justify-content: flex-end;
}

.edit-btn {
  font-size: 28rpx;
  color: #4a90d9;
}

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

.detail-content {
  flex: 1;
}

.cover-image {
  width: 100%;
  height: 360rpx;
}

.info-section {
  background: #fff;
  padding: 32rpx;
  margin-bottom: 16rpx;
}

.task-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #1a1a2e;
  display: block;
  margin-bottom: 16rpx;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.status-badge {
  font-size: 24rpx;
  padding: 6rpx 20rpx;
  border-radius: 20rpx;
  background: #f0f0f0;
  color: #666;

  &.status-pending {
    background: #f0f0f0;
    color: #666;
  }
  &.status-claimed,
  &.status-in_progress {
    background: #e6f7ff;
    color: #1890ff;
  }
  &.status-submitted {
    background: #fff7e6;
    color: #fa8c16;
  }
  &.status-approved {
    background: #f6ffed;
    color: #52c41a;
  }
  &.status-rejected {
    background: #fff1f0;
    color: #f5222d;
  }
  &.status-expired {
    background: #fff1f0;
    color: #f5222d;
  }
}

.type-badge {
  font-size: 24rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  background: #f5f6fa;
  color: #666;
}

.display-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
  display: block;
  margin-bottom: 12rpx;
}

.description {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
  display: block;
}

.section {
  background: #fff;
  padding: 32rpx;
  margin-bottom: 16rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.points-info {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.points-item {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 20rpx;
  border-radius: 12rpx;

  &.reward {
    background: #f6ffed;
  }
  &.penalty {
    background: #fff1f0;
  }
}

.points-icon {
  font-size: 32rpx;
}

.points-text {
  font-size: 28rpx;
  color: #333;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-label {
  font-size: 26rpx;
  color: #999;
}

.info-value {
  font-size: 26rpx;
  color: #333;
}

.safe-bottom {
  height: calc(160rpx + env(safe-area-inset-bottom));
}

.countdown-urgent {
  color: #f5222d !important;
  font-weight: 600;
}

.review-status-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx;
  border-radius: 12rpx;
  background: #f9f9fb;

  &.review-submitted {
    background: #fff7e6;
  }
  &.review-approved {
    background: #f6ffed;
  }
  &.review-rejected {
    background: #fff1f0;
  }
}

.review-icon {
  font-size: 40rpx;
}

.review-info {
  flex: 1;
}

.review-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 4rpx;
}

.review-hint {
  font-size: 24rpx;
  color: #666;
}

.action-bar {
  display: flex;
  gap: 20rpx;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.action-btn {
  flex: 1;
  height: 88rpx;
  font-size: 30rpx;
  font-weight: 600;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.primary {
    background: #4a90d9;
    color: #fff;
  }

  &.secondary {
    background: #f5f6fa;
    color: #4a90d9;
    border: 1rpx solid #4a90d9;
  }
}
</style>
