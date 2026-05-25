<template>
  <view class="points-page">
    <!-- 余额卡片 -->
    <view class="balance-card">
      <view class="balance-main">
        <text class="balance-label">当前积分</text>
        <text class="balance-value">{{ pointsStore.balance }}</text>
      </view>
      <view class="balance-secondary">
        <view class="balance-item">
          <text class="item-label">累计获得</text>
          <text class="item-value earned">+{{ pointsStore.totalEarned }}</text>
        </view>
        <view class="balance-divider" />
        <view class="balance-item">
          <text class="item-label">累计扣除</text>
          <text class="item-value spent">-{{ pointsStore.totalSpent }}</text>
        </view>
      </view>
    </view>

    <!-- Tab 切换 -->
    <view class="tab-bar">
      <view
        class="tab-item"
        :class="{ active: activeTab === 'history' }"
        @click="switchTab('history')"
      >
        <text>历史记录</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'leaderboard' }"
        @click="switchTab('leaderboard')"
      >
        <text>排行榜</text>
      </view>
    </view>

    <!-- 历史记录 Tab -->
    <view v-if="activeTab === 'history'" class="tab-content">
      <!-- 类型筛选 -->
      <view class="filter-bar">
        <view
          v-for="filter in filters"
          :key="filter.value"
          class="filter-btn"
          :class="{ active: currentFilter === filter.value }"
          @click="changeFilter(filter.value)"
        >
          <text>{{ filter.label }}</text>
        </view>
      </view>

      <!-- 历史列表 -->
      <scroll-view
        class="history-list"
        scroll-y
        refresher-enabled
        :refresher-triggered="isRefreshing"
        @refresherrefresh="handleRefresh"
        @scrolltolower="handleLoadMore"
      >
        <!-- 空状态 -->
        <view v-if="pointsStore.isHistoryEmpty" class="empty-state">
          <text class="empty-icon">📊</text>
          <text class="empty-text">暂无积分记录</text>
          <text class="empty-hint">完成任务即可获得积分奖励</text>
        </view>

        <!-- 时间线列表 -->
        <view
          v-for="item in pointsStore.history"
          :key="item.id"
          class="timeline-item"
        >
          <view class="timeline-indicator" :class="item.type === 'reward' ? 'indicator-reward' : 'indicator-penalty'">
            <text class="indicator-icon">{{ item.type === 'reward' ? '+' : '-' }}</text>
          </view>
          <view class="timeline-content">
            <view class="timeline-header">
              <text class="timeline-desc">{{ item.description || '积分变动' }}</text>
              <text class="timeline-amount" :class="item.type === 'reward' ? 'amount-reward' : 'amount-penalty'">
                {{ item.type === 'reward' ? '+' : '-' }}{{ Math.abs(item.amount) }}
              </text>
            </view>
            <text class="timeline-time">{{ formatTime(item.created_at) }}</text>
          </view>
        </view>

        <!-- 加载状态 -->
        <view v-if="pointsStore.loadingHistory && pointsStore.history.length > 0" class="loading-state">
          <text>加载中...</text>
        </view>

        <!-- 没有更多 -->
        <view v-if="!pointsStore.historyHasMore && pointsStore.history.length > 0" class="no-more">
          <text>没有更多了</text>
        </view>
      </scroll-view>
    </view>

    <!-- 排行榜 Tab -->
    <view v-if="activeTab === 'leaderboard'" class="tab-content">
      <scroll-view class="leaderboard-list" scroll-y>
        <!-- 空状态 -->
        <view v-if="pointsStore.isLeaderboardEmpty" class="empty-state">
          <text class="empty-icon">🏆</text>
          <text class="empty-text">暂无排行数据</text>
          <text class="empty-hint">家庭成员完成任务后将出现在排行榜</text>
        </view>

        <!-- 排行列表 -->
        <view
          v-for="(entry, index) in pointsStore.leaderboard"
          :key="entry.user_id"
          class="leaderboard-item"
          :class="{ 'top-three': index < 3 }"
        >
          <view class="rank-badge" :class="'rank-' + (index + 1)">
            <text class="rank-number">{{ index + 1 }}</text>
          </view>
          <view class="member-info">
            <text class="member-name">{{ entry.nickname || '未命名' }}</text>
            <text class="member-earned">累计获得 {{ entry.total_earned }}</text>
          </view>
          <view class="member-balance">
            <text class="balance-num">{{ entry.balance }}</text>
            <text class="balance-unit">积分</text>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePointsStore } from '@/stores/points'
import type { PointsTransactionType } from '@/services/types'

const pointsStore = usePointsStore()

const activeTab = ref<'history' | 'leaderboard'>('history')
const isRefreshing = ref(false)
const currentFilter = ref<string>('all')

const filters = [
  { label: '全部', value: 'all' },
  { label: '奖励', value: 'reward' },
  { label: '扣除', value: 'penalty' },
]

onMounted(() => {
  pointsStore.fetchBalance()
  pointsStore.fetchHistory()
})

function switchTab(tab: 'history' | 'leaderboard') {
  activeTab.value = tab
  if (tab === 'leaderboard' && pointsStore.leaderboard.length === 0) {
    pointsStore.fetchLeaderboard()
  }
}

function changeFilter(value: string) {
  currentFilter.value = value
  const type = value === 'all' ? undefined : (value as PointsTransactionType)
  pointsStore.fetchHistory(1, type)
}

async function handleRefresh() {
  isRefreshing.value = true
  try {
    await pointsStore.fetchBalance()
    const type = currentFilter.value === 'all' ? undefined : (currentFilter.value as PointsTransactionType)
    await pointsStore.fetchHistory(1, type)
  } finally {
    isRefreshing.value = false
  }
}

function handleLoadMore() {
  pointsStore.loadMoreHistory()
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

<style lang="scss" scoped>
.points-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f6fa;
}

/* 余额卡片 */
.balance-card {
  margin: 24rpx;
  padding: 40rpx 32rpx;
  background: linear-gradient(135deg, #4a90d9, #357abd);
  border-radius: 20rpx;
  color: #fff;
  box-shadow: 0 8rpx 24rpx rgba(74, 144, 217, 0.3);
}

.balance-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.balance-label {
  font-size: 26rpx;
  opacity: 0.85;
  margin-bottom: 12rpx;
}

.balance-value {
  font-size: 72rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.balance-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.2);
}

.balance-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.balance-divider {
  width: 1rpx;
  height: 48rpx;
  background: rgba(255, 255, 255, 0.3);
}

.item-label {
  font-size: 22rpx;
  opacity: 0.75;
  margin-bottom: 8rpx;
}

.item-value {
  font-size: 30rpx;
  font-weight: 600;

  &.earned {
    color: #a8e6cf;
  }

  &.spent {
    color: #ffb3b3;
  }
}

/* Tab 切换 */
.tab-bar {
  display: flex;
  background: #fff;
  padding: 0 32rpx;
  border-bottom: 1rpx solid #eee;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
  font-size: 28rpx;
  color: #999;
  position: relative;
  transition: color 0.2s;

  &.active {
    color: #4a90d9;
    font-weight: 600;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 48rpx;
      height: 4rpx;
      background: #4a90d9;
      border-radius: 2rpx;
    }
  }
}

/* Tab 内容区 */
.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  gap: 16rpx;
  padding: 20rpx 24rpx;
  background: #fff;
}

.filter-btn {
  padding: 10rpx 24rpx;
  border-radius: 24rpx;
  font-size: 24rpx;
  color: #666;
  background: #f5f6fa;
  transition: all 0.2s;

  &.active {
    background: #e6f0fa;
    color: #4a90d9;
    font-weight: 500;
  }
}

/* 历史列表 */
.history-list {
  flex: 1;
  padding: 16rpx 24rpx;
}

/* 时间线项 */
.timeline-item {
  display: flex;
  align-items: flex-start;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }
}

.timeline-indicator {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;

  &.indicator-reward {
    background: #f0fff4;
    border: 2rpx solid #52c41a;
  }

  &.indicator-penalty {
    background: #fff1f0;
    border: 2rpx solid #f5222d;
  }
}

.indicator-icon {
  font-size: 28rpx;
  font-weight: 700;

  .indicator-reward & {
    color: #52c41a;
  }

  .indicator-penalty & {
    color: #f5222d;
  }
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.timeline-desc {
  font-size: 28rpx;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-amount {
  font-size: 30rpx;
  font-weight: 600;
  margin-left: 16rpx;
  flex-shrink: 0;

  &.amount-reward {
    color: #52c41a;
  }

  &.amount-penalty {
    color: #f5222d;
  }
}

.timeline-time {
  font-size: 22rpx;
  color: #999;
}

/* 排行榜列表 */
.leaderboard-list {
  flex: 1;
  padding: 24rpx;
}

.leaderboard-item {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);

  &.top-three {
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
  }
}

.rank-badge {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  background: #f0f0f0;
  flex-shrink: 0;

  &.rank-1 {
    background: linear-gradient(135deg, #ffd700, #ffb800);
    box-shadow: 0 4rpx 12rpx rgba(255, 184, 0, 0.4);
  }

  &.rank-2 {
    background: linear-gradient(135deg, #c0c0c0, #a8a8a8);
    box-shadow: 0 4rpx 12rpx rgba(168, 168, 168, 0.4);
  }

  &.rank-3 {
    background: linear-gradient(135deg, #cd7f32, #b8690e);
    box-shadow: 0 4rpx 12rpx rgba(184, 105, 14, 0.4);
  }
}

.rank-number {
  font-size: 24rpx;
  font-weight: 700;
  color: #666;

  .rank-1 &,
  .rank-2 &,
  .rank-3 & {
    color: #fff;
  }
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  display: block;
  margin-bottom: 6rpx;
}

.member-earned {
  font-size: 22rpx;
  color: #999;
}

.member-balance {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
}

.balance-num {
  font-size: 32rpx;
  font-weight: 700;
  color: #4a90d9;
}

.balance-unit {
  font-size: 20rpx;
  color: #999;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 160rpx 0;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 30rpx;
  color: #666;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 24rpx;
  color: #999;
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 32rpx;
  color: #999;
  font-size: 26rpx;
}

.no-more {
  text-align: center;
  padding: 32rpx;
  color: #ccc;
  font-size: 24rpx;
}
</style>
