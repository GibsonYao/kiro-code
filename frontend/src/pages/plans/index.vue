<template>
  <view class="plans-page">
    <!-- 页面标题栏 -->
    <view class="page-header">
      <text class="page-title">我的计划</text>
      <view class="add-btn" @click="goToCreate">
        <text class="add-icon">+</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="planStore.loading && planStore.plans.length === 0" class="loading-state">
      <view class="skeleton-card" v-for="i in 4" :key="i">
        <view class="skeleton-image"></view>
        <view class="skeleton-text"></view>
        <view class="skeleton-text short"></view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="planStore.isEmpty" class="empty-state">
      <image class="empty-icon" src="/static/logo.png" mode="aspectFit" />
      <text class="empty-text">还没有计划</text>
      <text class="empty-hint">点击右上角 + 创建你的第一个执行计划</text>
      <view class="empty-btn" @click="goToCreate">
        <text>创建计划</text>
      </view>
    </view>

    <!-- 计划列表 -->
    <view v-else class="plan-list">
      <view
        v-for="plan in planStore.plans"
        :key="plan.id"
        class="plan-card"
        @click="goToDetail(plan.id)"
      >
        <!-- 配图 -->
        <view class="card-image-wrapper" v-if="plan.cover_image_url">
          <image
            class="card-image"
            :src="plan.cover_image_url"
            mode="aspectFill"
            lazy-load
          />
        </view>
        <view class="card-image-wrapper placeholder" v-else>
          <view class="placeholder-content">
            <text class="placeholder-emoji">📋</text>
          </view>
        </view>

        <!-- 卡片内容 -->
        <view class="card-body">
          <text class="card-title">{{ plan.display_text || plan.title }}</text>

          <!-- 时间范围 -->
          <view class="date-range" v-if="plan.start_date || plan.end_date">
            <text class="date-icon">📅</text>
            <text class="date-text">
              {{ plan.start_date || '未设置' }} ~ {{ plan.end_date || '未设置' }}
            </text>
          </view>

          <!-- 步骤概览 -->
          <view class="steps-overview" v-if="plan.steps.length > 0">
            <view class="steps-progress">
              <view class="steps-bar">
                <view
                  class="steps-fill"
                  :style="{ width: stepsProgress(plan) + '%' }"
                ></view>
              </view>
              <text class="steps-count">
                {{ completedSteps(plan) }}/{{ plan.steps.length }} 步骤
              </text>
            </view>
            <!-- 步骤标签 -->
            <view class="step-tags">
              <view
                v-for="step in plan.steps.slice(0, 3)"
                :key="step.id"
                class="step-tag"
                :class="{ bounty: step.is_bounty, action: step.step_type === 'action' }"
              >
                <text class="tag-icon">{{ step.is_bounty ? '🏆' : step.step_type === 'action' ? '⚡' : '✓' }}</text>
                <text class="tag-text">{{ step.title.slice(0, 8) }}{{ step.title.length > 8 ? '...' : '' }}</text>
              </view>
              <text v-if="plan.steps.length > 3" class="more-steps">+{{ plan.steps.length - 3 }}</text>
            </view>
          </view>

          <view class="card-footer">
            <text class="card-status" :class="plan.status">
              {{ statusLabel(plan.status) }}
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- 加载更多 -->
    <view v-if="planStore.hasMore" class="load-more" @click="planStore.loadMore()">
      <text v-if="planStore.loading">加载中...</text>
      <text v-else>加载更多</text>
    </view>

    <!-- 底部安全区 -->
    <view class="safe-bottom"></view>
  </view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { usePlanStore } from '@/stores/plan'
import type { PlanItem, PlanStatus } from '@/services/types'

const planStore = usePlanStore()

function statusLabel(status: PlanStatus): string {
  const map: Record<PlanStatus, string> = {
    draft: '草稿',
    active: '进行中',
    completed: '已完成',
    overdue: '已过期',
  }
  return map[status] || status
}

function completedSteps(plan: PlanItem): number {
  return plan.steps.filter(s => s.status === 'completed').length
}

function stepsProgress(plan: PlanItem): number {
  if (plan.steps.length === 0) return 0
  return Math.round((completedSteps(plan) / plan.steps.length) * 100)
}

function goToCreate(): void {
  uni.navigateTo({ url: '/pages/plans/create' })
}

function goToDetail(id: string): void {
  uni.navigateTo({ url: `/pages/plans/create?id=${id}` })
}

onMounted(() => {
  planStore.fetchPlans()
})

onPullDownRefresh(() => {
  planStore.fetchPlans().finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  planStore.loadMore()
})
</script>

<style lang="scss" scoped>
.plans-page {
  min-height: 100vh;
  background-color: #f5f6fa;
  padding: 24rpx;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32rpx;
}

.page-title {
  font-size: 40rpx;
  font-weight: 700;
  color: #1a1a2e;
}

.add-btn {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.4);
}

.add-icon {
  font-size: 40rpx;
  color: #fff;
  font-weight: 300;
}

// 计划列表
.plan-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.plan-card {
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: row;

  &:active {
    transform: scale(0.98);
  }
}

.card-image-wrapper {
  width: 200rpx;
  min-height: 200rpx;
  flex-shrink: 0;
  overflow: hidden;

  &.placeholder {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.placeholder-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-emoji {
  font-size: 56rpx;
}

.card-image {
  width: 100%;
  height: 100%;
}

.card-body {
  flex: 1;
  padding: 20rpx 24rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #1a1a2e;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8rpx;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 12rpx;
}

.date-icon {
  font-size: 22rpx;
}

.date-text {
  font-size: 22rpx;
  color: #999;
}

// 步骤概览
.steps-overview {
  margin-bottom: 12rpx;
}

.steps-progress {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.steps-bar {
  flex: 1;
  height: 8rpx;
  background: #f0f0f0;
  border-radius: 4rpx;
  overflow: hidden;
}

.steps-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4rpx;
  transition: width 0.3s ease;
}

.steps-count {
  font-size: 20rpx;
  color: #999;
  white-space: nowrap;
}

.step-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  align-items: center;
}

.step-tag {
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 4rpx 12rpx;
  background: #f5f5f5;
  border-radius: 12rpx;

  &.bounty {
    background: #fff3e0;
  }

  &.action {
    background: #e8f5e9;
  }
}

.tag-icon {
  font-size: 18rpx;
}

.tag-text {
  font-size: 20rpx;
  color: #666;
}

.more-steps {
  font-size: 20rpx;
  color: #999;
}

.card-footer {
  display: flex;
  align-items: center;
}

.card-status {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;

  &.draft {
    background: #f5f5f5;
    color: #9e9e9e;
  }

  &.active {
    background: #e8f5e9;
    color: #2e7d32;
  }

  &.completed {
    background: #e3f2fd;
    color: #1565c0;
  }

  &.overdue {
    background: #fbe9e7;
    color: #d84315;
  }
}

// 加载状态
.loading-state {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.skeleton-card {
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  padding: 24rpx;
  display: flex;
  gap: 16rpx;
}

.skeleton-image {
  width: 160rpx;
  height: 160rpx;
  border-radius: 16rpx;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-text {
  height: 24rpx;
  background: #f0f0f0;
  border-radius: 8rpx;
  flex: 1;

  &.short {
    width: 60%;
  }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200rpx;
}

.empty-icon {
  width: 160rpx;
  height: 160rpx;
  margin-bottom: 32rpx;
  opacity: 0.6;
}

.empty-text {
  font-size: 32rpx;
  color: #333;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: #999;
  margin-bottom: 48rpx;
}

.empty-btn {
  padding: 20rpx 48rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 40rpx;
  color: #fff;
  font-size: 28rpx;
}

// 加载更多
.load-more {
  text-align: center;
  padding: 32rpx;
  color: #999;
  font-size: 26rpx;
}

.safe-bottom {
  height: env(safe-area-inset-bottom);
}
</style>
