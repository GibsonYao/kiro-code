<template>
  <view class="goals-page">
    <!-- 页面标题栏 -->
    <view class="page-header">
      <text class="page-title">我的目标</text>
      <view class="add-btn" @click="goToCreate">
        <text class="add-icon">+</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="goalStore.loading && goalStore.goals.length === 0" class="loading-state">
      <view class="skeleton-card" v-for="i in 4" :key="i">
        <view class="skeleton-image"></view>
        <view class="skeleton-text"></view>
        <view class="skeleton-text short"></view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="goalStore.isEmpty" class="empty-state">
      <image class="empty-icon" src="/static/logo.png" mode="aspectFit" />
      <text class="empty-text">还没有目标</text>
      <text class="empty-hint">点击右上角 + 创建你的第一个SMART目标</text>
      <view class="empty-btn" @click="goToCreate">
        <text>创建目标</text>
      </view>
    </view>

    <!-- 瀑布流布局 -->
    <view v-else class="waterfall-container">
      <view class="waterfall-column" v-for="(column, colIdx) in columns" :key="colIdx">
        <view
          v-for="goal in column"
          :key="goal.id"
          class="goal-card"
          @click="goToDetail(goal.id)"
        >
          <!-- 配图 -->
          <view class="card-image-wrapper" v-if="goal.cover_image_url">
            <image
              class="card-image"
              :src="goal.cover_image_url"
              mode="widthFix"
              lazy-load
            />
          </view>
          <view class="card-image-wrapper placeholder" v-else>
            <view class="placeholder-content">
              <text class="placeholder-emoji">🎯</text>
              <text class="placeholder-text">配图生成中...</text>
            </view>
          </view>

          <!-- 卡片内容 -->
          <view class="card-content">
            <text class="card-title">{{ goal.display_text || goal.title }}</text>

            <!-- SMART描述摘要 -->
            <view class="smart-summary" v-if="goal.smart_specific">
              <text class="smart-tag">S</text>
              <text class="smart-text">{{ goal.smart_specific.slice(0, 40) }}{{ goal.smart_specific.length > 40 ? '...' : '' }}</text>
            </view>

            <!-- 进度条 -->
            <view class="progress-section">
              <view class="progress-bar">
                <view class="progress-fill" :style="{ width: goal.progress + '%' }"></view>
              </view>
              <text class="progress-text">{{ goal.progress }}%</text>
            </view>

            <view class="card-footer">
              <text class="card-status" :class="goal.status">
                {{ statusLabel(goal.status) }}
              </text>
              <text class="chain-link" @click.stop="goToChain(goal.id)">链路</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 加载更多 -->
    <view v-if="goalStore.hasMore" class="load-more" @click="goalStore.loadMore()">
      <text v-if="goalStore.loading">加载中...</text>
      <text v-else>加载更多</text>
    </view>

    <!-- 底部安全区 -->
    <view class="safe-bottom"></view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { useGoalStore } from '@/stores/goal'
import type { GoalItem, GoalStatus } from '@/services/types'

const goalStore = useGoalStore()

// 瀑布流双列布局
const columns = computed(() => {
  const col1: GoalItem[] = []
  const col2: GoalItem[] = []
  goalStore.goals.forEach((goal, index) => {
    if (index % 2 === 0) {
      col1.push(goal)
    } else {
      col2.push(goal)
    }
  })
  return [col1, col2]
})

function statusLabel(status: GoalStatus): string {
  const map: Record<GoalStatus, string> = {
    active: '进行中',
    completed: '已完成',
    archived: '已归档',
  }
  return map[status] || status
}

function goToCreate(): void {
  uni.navigateTo({ url: '/pages/goals/create' })
}

function goToDetail(id: string): void {
  uni.navigateTo({ url: `/pages/goals/create?id=${id}` })
}

function goToChain(id: string): void {
  uni.navigateTo({ url: `/pages/goals/chain?id=${id}` })
}

onMounted(() => {
  goalStore.fetchGoals()
})

// 下拉刷新
onPullDownRefresh(() => {
  goalStore.fetchGoals().finally(() => {
    uni.stopPullDownRefresh()
  })
})

// 触底加载更多
onReachBottom(() => {
  goalStore.loadMore()
})
</script>

<style lang="scss" scoped>
.goals-page {
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
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(67, 233, 123, 0.4);
}

.add-icon {
  font-size: 40rpx;
  color: #fff;
  font-weight: 300;
}

// 瀑布流
.waterfall-container {
  display: flex;
  gap: 20rpx;
}

.waterfall-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

// 目标卡片
.goal-card {
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

.card-image-wrapper {
  width: 100%;
  overflow: hidden;

  &.placeholder {
    height: 200rpx;
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.placeholder-emoji {
  font-size: 48rpx;
}

.placeholder-text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.9);
}

.card-image {
  width: 100%;
  display: block;
}

.card-content {
  padding: 20rpx 24rpx 24rpx;
}

.card-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #1a1a2e;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12rpx;
}

// SMART摘要
.smart-summary {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  margin-bottom: 12rpx;
}

.smart-tag {
  font-size: 20rpx;
  font-weight: 700;
  color: #fff;
  background: #43e97b;
  width: 32rpx;
  height: 32rpx;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.smart-text {
  font-size: 22rpx;
  color: #666;
  line-height: 1.4;
}

// 进度条
.progress-section {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.progress-bar {
  flex: 1;
  height: 12rpx;
  background: #f0f0f0;
  border-radius: 6rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #43e97b, #38f9d7);
  border-radius: 6rpx;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 22rpx;
  color: #999;
  min-width: 60rpx;
  text-align: right;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-status {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;

  &.active {
    background: #e8f5e9;
    color: #2e7d32;
  }

  &.completed {
    background: #e3f2fd;
    color: #1565c0;
  }

  &.archived {
    background: #f5f5f5;
    color: #9e9e9e;
  }
}

.chain-link {
  font-size: 22rpx;
  color: #667eea;
  padding: 4rpx 12rpx;
  border: 1rpx solid #667eea;
  border-radius: 16rpx;
}

// 加载状态
.loading-state {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.skeleton-card {
  width: calc(50% - 10rpx);
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  padding-bottom: 24rpx;
}

.skeleton-image {
  width: 100%;
  height: 200rpx;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-text {
  height: 24rpx;
  margin: 16rpx 24rpx 0;
  background: #f0f0f0;
  border-radius: 8rpx;

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
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
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
