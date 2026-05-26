<template>
  <view class="goal-detail-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">目标详情</text>
      <view class="nav-right">
        <text class="chain-btn" @click="goChain">链路</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 目标内容 -->
    <scroll-view v-else-if="goal" class="detail-content" scroll-y>
      <!-- 封面图 -->
      <image
        v-if="goal.cover_image_url"
        :src="goal.cover_image_url"
        class="cover-image"
        mode="aspectFill"
      />

      <!-- 基本信息 -->
      <view class="info-section">
        <text class="goal-title">{{ goal.title }}</text>
        <view class="status-row">
          <view class="status-badge" :class="'status-' + goal.status">
            {{ statusLabel(goal.status) }}
          </view>
        </view>
        <text v-if="goal.display_text" class="display-text">{{ goal.display_text }}</text>
        <text v-if="goal.description" class="description">{{ goal.description }}</text>
      </view>

      <!-- 进度条 -->
      <view class="section">
        <text class="section-title">完成进度</text>
        <view class="progress-container">
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: goal.progress + '%' }" />
          </view>
          <text class="progress-text">{{ goal.progress }}%</text>
        </view>
      </view>

      <!-- SMART 描述 -->
      <view class="section" v-if="hasSmart">
        <text class="section-title">SMART 目标分析</text>
        <view class="smart-list">
          <view v-if="goal.smart_specific" class="smart-item">
            <view class="smart-label-row">
              <text class="smart-icon">🎯</text>
              <text class="smart-label">具体的 (Specific)</text>
            </view>
            <text class="smart-value">{{ goal.smart_specific }}</text>
          </view>
          <view v-if="goal.smart_measurable" class="smart-item">
            <view class="smart-label-row">
              <text class="smart-icon">📏</text>
              <text class="smart-label">可衡量的 (Measurable)</text>
            </view>
            <text class="smart-value">{{ goal.smart_measurable }}</text>
          </view>
          <view v-if="goal.smart_achievable" class="smart-item">
            <view class="smart-label-row">
              <text class="smart-icon">✅</text>
              <text class="smart-label">可实现的 (Achievable)</text>
            </view>
            <text class="smart-value">{{ goal.smart_achievable }}</text>
          </view>
          <view v-if="goal.smart_relevant" class="smart-item">
            <view class="smart-label-row">
              <text class="smart-icon">🔗</text>
              <text class="smart-label">相关的 (Relevant)</text>
            </view>
            <text class="smart-value">{{ goal.smart_relevant }}</text>
          </view>
          <view v-if="goal.smart_time_bound" class="smart-item">
            <view class="smart-label-row">
              <text class="smart-icon">⏰</text>
              <text class="smart-label">有时限的 (Time-bound)</text>
            </view>
            <text class="smart-value">{{ goal.smart_time_bound }}</text>
          </view>
        </view>
      </view>

      <!-- 关联计划 -->
      <view class="section">
        <text class="section-title">关联计划</text>
        <view v-if="relatedPlans.length > 0" class="plans-list">
          <view
            v-for="plan in relatedPlans"
            :key="plan.id"
            class="plan-card"
            @click="goPlanDetail(plan.id)"
          >
            <view class="plan-info">
              <text class="plan-title">{{ plan.title }}</text>
              <view class="plan-meta">
                <text class="plan-status" :class="'ps-' + plan.status">{{ planStatusLabel(plan.status) }}</text>
                <text v-if="plan.start_date" class="plan-date">{{ plan.start_date }} ~ {{ plan.end_date || '未定' }}</text>
              </view>
            </view>
            <text class="plan-arrow">›</text>
          </view>
        </view>
        <view v-else class="empty-state">
          <text class="empty-text">暂无关联计划</text>
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
import { goalApi } from '@/services/api/goals'
import { planApi } from '@/services/api/plans'
import type { GoalItem, PlanItem } from '@/services/types'

const goal = ref<GoalItem | null>(null)
const relatedPlans = ref<PlanItem[]>([])
const loading = ref(true)
let goalId = ''

const hasSmart = computed(() => {
  if (!goal.value) return false
  return goal.value.smart_specific || goal.value.smart_measurable ||
    goal.value.smart_achievable || goal.value.smart_relevant || goal.value.smart_time_bound
})

onLoad((query) => {
  const id = query?.id
  if (id) {
    goalId = id
    loadGoal(id)
    loadRelatedPlans(id)
  }
})

async function loadGoal(id: string) {
  loading.value = true
  try {
    goal.value = await goalApi.getGoal(id)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadRelatedPlans(goalIdParam: string) {
  try {
    const res = await planApi.getPlans({ page: 1, page_size: 50 })
    relatedPlans.value = res.items.filter(p => p.goal_id === goalIdParam)
  } catch {
    // Silently fail
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    active: '进行中',
    completed: '已完成',
    archived: '已归档',
  }
  return map[status] || status
}

function planStatusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '进行中',
    completed: '已完成',
    overdue: '已逾期',
  }
  return map[status] || status
}

function goPlanDetail(id: string) {
  uni.navigateTo({ url: `/pages/plans/detail?id=${id}` })
}

function goChain() {
  uni.navigateTo({ url: `/pages/goals/chain?id=${goalId}` })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.goal-detail-page {
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
  display: flex;
  justify-content: flex-end;
}

.chain-btn {
  font-size: 28rpx;
  color: #fff;
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

.goal-title {
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

  &.status-active {
    background: #e6f7ff;
    color: #1890ff;
  }
  &.status-completed {
    background: #f6ffed;
    color: #52c41a;
  }
  &.status-archived {
    background: #f0f0f0;
    color: #999;
  }
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

.progress-container {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.progress-bar {
  flex: 1;
  height: 16rpx;
  background: #e8e8e8;
  border-radius: 8rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 8rpx;
  transition: width 0.3s;
}

.progress-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #667eea;
  min-width: 80rpx;
  text-align: right;
}

.smart-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.smart-item {
  padding: 20rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.smart-label-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.smart-icon {
  font-size: 28rpx;
}

.smart-label {
  font-size: 24rpx;
  color: #666;
  font-weight: 500;
}

.smart-value {
  font-size: 26rpx;
  color: #333;
  line-height: 1.6;
  display: block;
  padding-left: 40rpx;
}

.plans-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.plan-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.plan-info {
  flex: 1;
}

.plan-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  display: block;
  margin-bottom: 8rpx;
}

.plan-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.plan-status {
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  background: #f0f0f0;
  color: #666;

  &.ps-active {
    background: #e6f7ff;
    color: #1890ff;
  }
  &.ps-completed {
    background: #f6ffed;
    color: #52c41a;
  }
  &.ps-overdue {
    background: #fff1f0;
    color: #f5222d;
  }
}

.plan-date {
  font-size: 22rpx;
  color: #999;
}

.plan-arrow {
  font-size: 32rpx;
  color: #ccc;
  margin-left: 16rpx;
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
