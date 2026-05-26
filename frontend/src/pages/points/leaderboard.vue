<template>
  <view class="leaderboard-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">积分排行榜</text>
      <view class="nav-right" />
    </view>

    <!-- 加载状态 -->
    <view v-if="pointsStore.loadingLeaderboard" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 排行榜 -->
    <scroll-view v-else class="leaderboard-content" scroll-y>
      <!-- 前三名 -->
      <view v-if="topThree.length > 0" class="podium-section">
        <view class="podium">
          <!-- 第二名 -->
          <view v-if="topThree[1]" class="podium-item second">
            <view class="podium-avatar-wrap">
              <text class="podium-rank">2</text>
              <view class="podium-avatar">
                <text class="avatar-text">{{ getInitial(topThree[1].nickname) }}</text>
              </view>
            </view>
            <text class="podium-name" :class="{ 'is-me': isCurrentUser(topThree[1].user_id) }">
              {{ topThree[1].nickname || '匿名' }}
            </text>
            <text class="podium-points">{{ topThree[1].total_earned }} 分</text>
          </view>

          <!-- 第一名 -->
          <view v-if="topThree[0]" class="podium-item first">
            <view class="podium-avatar-wrap">
              <text class="podium-crown">👑</text>
              <view class="podium-avatar gold">
                <text class="avatar-text">{{ getInitial(topThree[0].nickname) }}</text>
              </view>
            </view>
            <text class="podium-name" :class="{ 'is-me': isCurrentUser(topThree[0].user_id) }">
              {{ topThree[0].nickname || '匿名' }}
            </text>
            <text class="podium-points">{{ topThree[0].total_earned }} 分</text>
          </view>

          <!-- 第三名 -->
          <view v-if="topThree[2]" class="podium-item third">
            <view class="podium-avatar-wrap">
              <text class="podium-rank">3</text>
              <view class="podium-avatar">
                <text class="avatar-text">{{ getInitial(topThree[2].nickname) }}</text>
              </view>
            </view>
            <text class="podium-name" :class="{ 'is-me': isCurrentUser(topThree[2].user_id) }">
              {{ topThree[2].nickname || '匿名' }}
            </text>
            <text class="podium-points">{{ topThree[2].total_earned }} 分</text>
          </view>
        </view>
      </view>

      <!-- 其余排名 -->
      <view class="rank-list">
        <view
          v-for="(entry, index) in restEntries"
          :key="entry.user_id"
          class="rank-item"
          :class="{ 'is-me': isCurrentUser(entry.user_id) }"
        >
          <text class="rank-number">{{ index + 4 }}</text>
          <view class="rank-avatar">
            <text class="avatar-text-sm">{{ getInitial(entry.nickname) }}</text>
          </view>
          <view class="rank-info">
            <text class="rank-name">{{ entry.nickname || '匿名' }}</text>
            <text class="rank-balance">当前余额: {{ entry.balance }}</text>
          </view>
          <text class="rank-points">{{ entry.total_earned }} 分</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="pointsStore.leaderboard.length === 0" class="empty-state">
        <text class="empty-icon">🏆</text>
        <text class="empty-text">暂无排行数据</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { usePointsStore } from '@/stores/points'
import { useUserStore } from '@/stores/user'

const pointsStore = usePointsStore()
const userStore = useUserStore()

const topThree = computed(() => pointsStore.leaderboard.slice(0, 3))
const restEntries = computed(() => pointsStore.leaderboard.slice(3))

onLoad(() => {
  pointsStore.fetchLeaderboard()
})

function isCurrentUser(userId: string): boolean {
  return userId === userStore.userId
}

function getInitial(name: string | null): string {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.leaderboard-page {
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

.leaderboard-content {
  flex: 1;
}

.podium-section {
  background: linear-gradient(180deg, #fff8e1 0%, #fff 100%);
  padding: 48rpx 32rpx;
}

.podium {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 24rpx;
}

.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 180rpx;

  &.first {
    margin-bottom: 24rpx;
  }
  &.second,
  &.third {
    margin-bottom: 0;
  }
}

.podium-avatar-wrap {
  position: relative;
  margin-bottom: 12rpx;
}

.podium-crown {
  position: absolute;
  top: -32rpx;
  left: 50%;
  transform: translateX(-50%);
  font-size: 36rpx;
}

.podium-rank {
  position: absolute;
  top: -16rpx;
  left: 50%;
  transform: translateX(-50%);
  font-size: 24rpx;
  font-weight: 700;
  color: #fa8c16;
  background: #fff;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.podium-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid #e8e8e8;

  &.gold {
    border-color: #ffd700;
    width: 112rpx;
    height: 112rpx;
  }
}

.avatar-text {
  font-size: 36rpx;
  color: #fff;
  font-weight: 700;
}

.podium-name {
  font-size: 24rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 4rpx;
  max-width: 160rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  &.is-me {
    color: #4a90d9;
    font-weight: 700;
  }
}

.podium-points {
  font-size: 22rpx;
  color: #fa8c16;
  font-weight: 600;
}

.rank-list {
  background: #fff;
  padding: 0 32rpx;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }

  &.is-me {
    background: #f0f7ff;
    margin: 0 -32rpx;
    padding: 24rpx 32rpx;
    border-radius: 12rpx;
  }
}

.rank-number {
  width: 48rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #999;
  text-align: center;
}

.rank-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 16rpx;
}

.avatar-text-sm {
  font-size: 26rpx;
  color: #fff;
  font-weight: 600;
}

.rank-info {
  flex: 1;
}

.rank-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  display: block;
  margin-bottom: 4rpx;
}

.rank-balance {
  font-size: 22rpx;
  color: #999;
}

.rank-points {
  font-size: 28rpx;
  font-weight: 700;
  color: #fa8c16;
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

.safe-bottom {
  height: calc(48rpx + env(safe-area-inset-bottom));
}
</style>
