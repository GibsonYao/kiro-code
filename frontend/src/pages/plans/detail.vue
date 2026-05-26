<template>
  <view class="plan-detail-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">计划详情</text>
      <view class="nav-right" />
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 计划内容 -->
    <scroll-view v-else-if="plan" class="detail-content" scroll-y>
      <!-- 封面图 -->
      <image
        v-if="plan.cover_image_url"
        :src="plan.cover_image_url"
        class="cover-image"
        mode="aspectFill"
      />

      <!-- 基本信息 -->
      <view class="info-section">
        <text class="plan-title">{{ plan.title }}</text>
        <view class="status-row">
          <view class="status-badge" :class="'status-' + plan.status">
            {{ statusLabel(plan.status) }}
          </view>
        </view>
        <text v-if="plan.display_text" class="display-text">{{ plan.display_text }}</text>
      </view>

      <!-- 时间进度 -->
      <view class="section" v-if="plan.start_date || plan.end_date">
        <text class="section-title">时间进度</text>
        <view class="time-info">
          <view class="time-row">
            <text class="time-label">开始日期</text>
            <text class="time-value">{{ plan.start_date || '未设置' }}</text>
          </view>
          <view class="time-row">
            <text class="time-label">结束日期</text>
            <text class="time-value">{{ plan.end_date || '未设置' }}</text>
          </view>
          <view v-if="timeProgress >= 0" class="time-progress">
            <view class="progress-bar">
              <view class="progress-fill" :style="{ width: Math.min(timeProgress, 100) + '%' }" />
            </view>
            <text class="progress-text">{{ timeProgressText }}</text>
          </view>
        </view>
      </view>

      <!-- 负责人 -->
      <view class="section">
        <text class="section-title">负责人</text>
        <view class="owner-info">
          <text class="owner-icon">👤</text>
          <text class="owner-name">{{ plan.owner_id ? '已分配' : '未分配' }}</text>
        </view>
      </view>

      <!-- 步骤列表 -->
      <view class="section">
        <text class="section-title">执行步骤</text>
        <view v-if="plan.steps && plan.steps.length > 0" class="steps-list">
          <view
            v-for="(step, index) in plan.steps"
            :key="step.id"
            class="step-item"
          >
            <view class="step-indicator" :class="'si-' + step.status">
              <text class="step-number">{{ index + 1 }}</text>
            </view>
            <view class="step-content">
              <text class="step-title">{{ step.title }}</text>
              <view class="step-meta">
                <text class="step-type">{{ step.step_type === 'task' ? '📋 任务' : '⚡ 行动' }}</text>
                <text v-if="step.is_bounty" class="step-bounty">🎁 悬赏</text>
                <text class="step-status" :class="'ss-' + step.status">{{ stepStatusLabel(step.status) }}</text>
              </view>
            </view>
          </view>
        </view>
        <view v-else class="empty-state">
          <text class="empty-text">暂无步骤</text>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { planApi } from '@/services/api/plans'
import type { PlanItem } from '@/services/types'

const plan = ref<PlanItem | null>(null)
const loading = ref(true)

const timeProgress = computed(() => {
  if (!plan.value?.start_date || !plan.value?.end_date) return -1
  const start = new Date(plan.value.start_date).getTime()
  const end = new Date(plan.value.end_date).getTime()
  const now = Date.now()
  if (end <= start) return 0
  return Math.round(((now - start) / (end - start)) * 100)
})

const timeProgressText = computed(() => {
  if (timeProgress.value < 0) return ''
  if (timeProgress.value >= 100) return '已到期'
  return `已过 ${timeProgress.value}%`
})

onLoad((query) => {
  const id = query?.id
  if (id) {
    loadPlan(id)
  }
})

async function loadPlan(id: string) {
  loading.value = true
  try {
    plan.value = await planApi.getPlan(id)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '进行中',
    completed: '已完成',
    overdue: '已逾期',
  }
  return map[status] || status
}

function stepStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待开始',
    in_progress: '进行中',
    completed: '已完成',
  }
  return map[status] || status
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.plan-detail-page {
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.nav-back {
  width: 64rpx;
}

.back-icon {
  font-size: 36rpx;
  color: #fff;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #fff;
}

.nav-right {
  width: 64rpx;
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

.plan-title {
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
  margin-bottom: 16rpx;
}

.status-badge {
  font-size: 24rpx;
  padding: 6rpx 20rpx;
  border-radius: 20rpx;
  background: #f0f0f0;
  color: #666;

  &.status-draft {
    background: #f0f0f0;
    color: #666;
  }
  &.status-active {
    background: #e6f7ff;
    color: #1890ff;
  }
  &.status-completed {
    background: #f6ffed;
    color: #52c41a;
  }
  &.status-overdue {
    background: #fff1f0;
    color: #f5222d;
  }
}

.display-text {
  font-size: 28rpx;
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

.time-info {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.time-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.time-label {
  font-size: 26rpx;
  color: #999;
}

.time-value {
  font-size: 26rpx;
  color: #333;
}

.time-progress {
  margin-top: 12rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.progress-bar {
  flex: 1;
  height: 12rpx;
  background: #e8e8e8;
  border-radius: 6rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 6rpx;
  transition: width 0.3s;
}

.progress-text {
  font-size: 24rpx;
  color: #667eea;
  min-width: 100rpx;
  text-align: right;
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 20rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.owner-icon {
  font-size: 32rpx;
}

.owner-name {
  font-size: 28rpx;
  color: #333;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.step-item {
  display: flex;
  align-items: flex-start;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.step-indicator {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  flex-shrink: 0;
  background: #e8e8e8;

  &.si-pending {
    background: #f0f0f0;
  }
  &.si-in_progress {
    background: #e6f7ff;
  }
  &.si-completed {
    background: #f6ffed;
  }
}

.step-number {
  font-size: 22rpx;
  font-weight: 600;
  color: #666;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  display: block;
  margin-bottom: 8rpx;
}

.step-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.step-type {
  font-size: 22rpx;
  color: #666;
}

.step-bounty {
  font-size: 22rpx;
  color: #fa8c16;
}

.step-status {
  font-size: 22rpx;
  padding: 2rpx 10rpx;
  border-radius: 6rpx;
  background: #f0f0f0;
  color: #666;

  &.ss-in_progress {
    background: #e6f7ff;
    color: #1890ff;
  }
  &.ss-completed {
    background: #f6ffed;
    color: #52c41a;
  }
}

.empty-state {
  padding: 24rpx 0;
}

.empty-text {
  font-size: 26rpx;
  color: #999;
}

.safe-bottom {
  height: calc(48rpx + env(safe-area-inset-bottom));
}
</style>
