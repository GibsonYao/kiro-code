<template>
  <view class="chain-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">目标链路</text>
      <view class="nav-right"></view>
    </view>

    <!-- 加载状态 -->
    <view v-if="goalStore.chainLoading" class="loading-state">
      <view class="loading-spinner">
        <text class="spinner-dot">●</text>
        <text class="spinner-dot delay-1">●</text>
        <text class="spinner-dot delay-2">●</text>
      </view>
      <text class="loading-text">加载链路中...</text>
    </view>

    <!-- 链路内容 -->
    <ChainView v-else-if="chain" :chain-data="chain" class="chain-content" />

    <!-- 空状态 -->
    <view v-else class="error-state">
      <text class="error-text">加载失败</text>
      <view class="retry-btn" @click="loadChain">
        <text>重试</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useGoalStore } from '@/stores/goal'
import ChainView from '@/components/ChainView.vue'

const goalStore = useGoalStore()
let currentGoalId = ''

const chain = computed(() => goalStore.currentGoalChain)

onLoad((query) => {
  const id = query?.id
  if (id) {
    currentGoalId = id
    loadChain()
  }
})

function loadChain(): void {
  if (currentGoalId) {
    goalStore.fetchGoalChain(currentGoalId)
  }
}

function goBack(): void {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.chain-page {
  min-height: 100vh;
  background-color: #f5f6fa;
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
}

// 加载状态
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200rpx;
}

.loading-spinner {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.spinner-dot {
  font-size: 24rpx;
  color: #667eea;
  animation: pulse 1.4s infinite;

  &.delay-1 { animation-delay: 0.2s; }
  &.delay-2 { animation-delay: 0.4s; }
}

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

// 链路内容
.chain-content {
  height: calc(100vh - 100rpx);
}

// 错误状态
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200rpx;
}

.error-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 24rpx;
}

.retry-btn {
  padding: 16rpx 40rpx;
  background: #667eea;
  border-radius: 32rpx;
  color: #fff;
  font-size: 28rpx;
}
</style>
