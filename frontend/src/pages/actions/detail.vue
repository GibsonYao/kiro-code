<template>
  <view class="action-detail-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">行动详情</text>
      <view class="nav-right">
        <text v-if="canEdit" class="edit-btn" @click="goEdit">编辑</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 行动内容 -->
    <scroll-view v-else-if="action" class="detail-content" scroll-y>
      <!-- 封面图 -->
      <image
        v-if="action.cover_image_url"
        :src="action.cover_image_url"
        class="cover-image"
        mode="aspectFill"
      />

      <!-- 基本信息 -->
      <view class="info-section">
        <text class="action-title">{{ action.title }}</text>
        <view class="status-row">
          <view class="status-badge" :class="'status-' + action.status">
            {{ statusLabel(action.status) }}
          </view>
          <view class="type-badge">
            {{ action.action_type === 'todo' ? '✅ 待办' : '📅 日程' }}
          </view>
        </view>
        <text v-if="action.display_text" class="display-text">{{ action.display_text }}</text>
      </view>

      <!-- 日程信息 -->
      <view class="section" v-if="action.action_type === 'schedule'">
        <text class="section-title">日程安排</text>
        <view class="info-list">
          <view v-if="action.scheduled_date" class="info-row">
            <text class="info-label">日期</text>
            <text class="info-value">{{ action.scheduled_date }}</text>
          </view>
          <view v-if="action.scheduled_time" class="info-row">
            <text class="info-label">时间</text>
            <text class="info-value">{{ action.scheduled_time }}</text>
          </view>
        </view>
      </view>

      <!-- 关联任务 -->
      <view class="section" v-if="action.task_id">
        <text class="section-title">关联任务</text>
        <view class="related-task-card" @click="goTaskDetail">
          <text class="related-icon">📋</text>
          <text class="related-text">查看关联任务</text>
          <text class="related-arrow">›</text>
        </view>
      </view>

      <!-- 执行信息 -->
      <view class="section">
        <text class="section-title">执行信息</text>
        <view class="info-list">
          <view v-if="action.time_spent_minutes" class="info-row">
            <text class="info-label">已花费时间</text>
            <text class="info-value">{{ action.time_spent_minutes }} 分钟</text>
          </view>
          <view v-if="action.reward_points" class="info-row">
            <text class="info-label">奖励积分</text>
            <text class="info-value reward">+{{ action.reward_points }} 分</text>
          </view>
          <view class="info-row">
            <text class="info-label">创建时间</text>
            <text class="info-value">{{ formatDate(action.created_at) }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">更新时间</text>
            <text class="info-value">{{ formatDate(action.updated_at) }}</text>
          </view>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom"></view>
    </scroll-view>

    <!-- 底部操作栏 -->
    <view v-if="action && canComplete" class="action-bar">
      <button class="action-btn primary" @click="handleComplete">
        标记完成
      </button>
      <button class="action-btn secondary" @click="goEdit">
        编辑行动
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { actionApi } from '@/services/api/actions'
import { useActionStore } from '@/stores/action'
import type { ActionItem } from '@/services/types'

const actionStore = useActionStore()
const action = ref<ActionItem | null>(null)
const loading = ref(true)
let actionId = ''

const canEdit = computed(() => {
  if (!action.value) return false
  return ['pending', 'in_progress', 'rejected'].includes(action.value.status)
})

const canComplete = computed(() => {
  if (!action.value) return false
  return ['pending', 'in_progress', 'rejected'].includes(action.value.status)
})

onLoad((query) => {
  const id = query?.id
  if (id) {
    actionId = id
    loadAction(id)
  }
})

async function loadAction(id: string) {
  loading.value = true
  try {
    action.value = await actionApi.getAction(id)
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
  uni.navigateTo({ url: `/pages/actions/create?id=${actionId}` })
}

function goTaskDetail() {
  if (action.value?.task_id) {
    uni.navigateTo({ url: `/pages/tasks/detail?id=${action.value.task_id}` })
  }
}

async function handleComplete() {
  try {
    const updated = await actionStore.completeAction(actionId)
    action.value = updated
    uni.showToast({ title: '已标记完成', icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    submitted: '待审核',
    approved: '已完成',
    rejected: '已驳回',
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
.action-detail-page {
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

.action-title {
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
}

.related-task-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.related-icon {
  font-size: 32rpx;
  margin-right: 12rpx;
}

.related-text {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.related-arrow {
  font-size: 32rpx;
  color: #ccc;
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

  &.reward {
    color: #52c41a;
    font-weight: 500;
  }
}

.safe-bottom {
  height: calc(160rpx + env(safe-area-inset-bottom));
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
