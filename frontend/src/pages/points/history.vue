<template>
  <view class="points-history-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">积分明细</text>
      <view class="nav-right" />
    </view>

    <!-- 筛选栏 -->
    <view class="filter-bar">
      <!-- 类型筛选 -->
      <view class="filter-tabs">
        <view
          class="filter-tab"
          :class="{ active: currentType === '' }"
          @click="switchType('')"
        >
          <text>全部</text>
        </view>
        <view
          class="filter-tab"
          :class="{ active: currentType === 'reward' }"
          @click="switchType('reward')"
        >
          <text>获得</text>
        </view>
        <view
          class="filter-tab"
          :class="{ active: currentType === 'penalty' }"
          @click="switchType('penalty')"
        >
          <text>扣除</text>
        </view>
        <view
          class="filter-tab"
          :class="{ active: currentType === 'manual_adjust' }"
          @click="switchType('manual_adjust')"
        >
          <text>调整</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view
      class="history-list"
      scroll-y
      @scrolltolower="handleLoadMore"
    >
      <view v-if="pointsStore.loadingHistory && pointsStore.history.length === 0" class="loading-state">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="pointsStore.history.length === 0" class="empty-state">
        <text class="empty-icon">📊</text>
        <text class="empty-text">暂无积分记录</text>
      </view>

      <view v-else class="timeline">
        <view
          v-for="item in pointsStore.history"
          :key="item.id"
          class="timeline-item"
        >
          <view class="timeline-dot" :class="item.amount >= 0 ? 'dot-positive' : 'dot-negative'" />
          <view class="timeline-content">
            <view class="item-header">
              <text class="item-desc">{{ item.description || typeLabel(item.type) }}</text>
              <text class="item-amount" :class="item.amount >= 0 ? 'amount-positive' : 'amount-negative'">
                {{ item.amount >= 0 ? '+' : '' }}{{ item.amount }}
              </text>
            </view>
            <view class="item-footer">
              <text class="item-type">{{ typeLabel(item.type) }}</text>
              <text class="item-time">{{ formatTime(item.created_at) }}</text>
            </view>
            <text class="item-balance">余额: {{ item.balance_after }}</text>
          </view>
        </view>
      </view>

      <!-- 加载更多 -->
      <view v-if="pointsStore.historyHasMore" class="load-more">
        <text class="load-more-text">{{ pointsStore.loadingHistory ? '加载中...' : '上拉加载更多' }}</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { usePointsStore } from '@/stores/points'
import type { PointsTransactionType } from '@/services/types'

const pointsStore = usePointsStore()
const currentType = ref('')

onLoad(() => {
  pointsStore.fetchHistory(1)
})

function switchType(type: string) {
  currentType.value = type
  const typeParam = type ? type as PointsTransactionType : undefined
  pointsStore.fetchHistory(1, typeParam)
}

function handleLoadMore() {
  pointsStore.loadMoreHistory()
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    reward: '奖励',
    penalty: '扣除',
    manual_adjust: '手动调整',
  }
  return map[type] || type
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.points-history-page {
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
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
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

.filter-bar {
  background: #fff;
  padding: 20rpx 32rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.filter-tabs {
  display: flex;
  gap: 16rpx;
}

.filter-tab {
  padding: 12rpx 24rpx;
  border-radius: 24rpx;
  background: #f5f6fa;
  font-size: 26rpx;
  color: #666;

  &.active {
    background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
    color: #fff;
  }
}

.history-list {
  flex: 1;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 16rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

.timeline {
  padding: 24rpx 32rpx;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.timeline-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  margin-top: 12rpx;
  margin-right: 20rpx;
  flex-shrink: 0;

  &.dot-positive {
    background: #52c41a;
  }
  &.dot-negative {
    background: #f5222d;
  }
}

.timeline-content {
  flex: 1;
  background: #fff;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.item-desc {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  flex: 1;
}

.item-amount {
  font-size: 32rpx;
  font-weight: 700;

  &.amount-positive {
    color: #52c41a;
  }
  &.amount-negative {
    color: #f5222d;
  }
}

.item-footer {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 4rpx;
}

.item-type {
  font-size: 22rpx;
  padding: 2rpx 10rpx;
  border-radius: 6rpx;
  background: #f5f6fa;
  color: #666;
}

.item-time {
  font-size: 22rpx;
  color: #999;
}

.item-balance {
  font-size: 22rpx;
  color: #bbb;
}

.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}

.load-more-text {
  font-size: 24rpx;
  color: #999;
}

.safe-bottom {
  height: calc(48rpx + env(safe-area-inset-bottom));
}
</style>
