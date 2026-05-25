<template>
  <view class="wishes-page">
    <!-- 页面标题栏 -->
    <view class="page-header">
      <text class="page-title">我的愿望</text>
      <view class="add-btn" @click="goToCreate">
        <text class="add-icon">+</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="wishStore.loading && wishStore.wishes.length === 0" class="loading-state">
      <view class="skeleton-card" v-for="i in 4" :key="i">
        <view class="skeleton-image"></view>
        <view class="skeleton-text"></view>
        <view class="skeleton-text short"></view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="wishStore.isEmpty" class="empty-state">
      <image class="empty-icon" src="/static/logo.png" mode="aspectFit" />
      <text class="empty-text">还没有愿望</text>
      <text class="empty-hint">点击右上角 + 创建你的第一个愿望</text>
      <view class="empty-btn" @click="goToCreate">
        <text>创建愿望</text>
      </view>
    </view>

    <!-- 瀑布流布局 -->
    <view v-else class="waterfall-container">
      <view class="waterfall-column" v-for="(column, colIdx) in columns" :key="colIdx">
        <view
          v-for="wish in column"
          :key="wish.id"
          class="wish-card"
          @click="goToDetail(wish.id)"
        >
          <!-- 愿景图 -->
          <view class="card-image-wrapper" v-if="wish.vision_image_url || wish.cover_image_url">
            <image
              class="card-image"
              :src="wish.vision_image_url || wish.cover_image_url"
              mode="widthFix"
              lazy-load
            />
          </view>
          <view class="card-image-wrapper placeholder" v-else>
            <view class="placeholder-content">
              <text class="placeholder-emoji">✨</text>
              <text class="placeholder-text">愿景生成中...</text>
            </view>
          </view>

          <!-- 卡片内容 -->
          <view class="card-content">
            <text class="card-title">{{ wish.display_text || wish.title }}</text>
            <text class="card-story" v-if="wish.vision_story">
              {{ wish.vision_story.slice(0, 60) }}{{ wish.vision_story.length > 60 ? '...' : '' }}
            </text>
            <view class="card-footer">
              <text class="card-status" :class="wish.status">
                {{ statusLabel(wish.status) }}
              </text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 加载更多 -->
    <view v-if="wishStore.hasMore" class="load-more" @click="wishStore.loadMore()">
      <text v-if="wishStore.loading">加载中...</text>
      <text v-else>加载更多</text>
    </view>

    <!-- 底部安全区 -->
    <view class="safe-bottom"></view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { useWishStore } from '@/stores/wish'
import type { WishItem } from '@/services/types'
import type { WishStatus } from '@/services/types'

const wishStore = useWishStore()

// 瀑布流双列布局
const columns = computed(() => {
  const col1: WishItem[] = []
  const col2: WishItem[] = []
  wishStore.wishes.forEach((wish, index) => {
    if (index % 2 === 0) {
      col1.push(wish)
    } else {
      col2.push(wish)
    }
  })
  return [col1, col2]
})

function statusLabel(status: WishStatus): string {
  const map: Record<WishStatus, string> = {
    active: '进行中',
    achieved: '已实现',
    archived: '已归档',
  }
  return map[status] || status
}

function goToCreate(): void {
  uni.navigateTo({ url: '/pages/wishes/create' })
}

function goToDetail(id: string | Record<string, unknown>): void {
  // Ensure id is a plain string (API may return UUID object in some environments)
  const idStr = typeof id === 'object' ? String(id) : id
  if (!idStr || idStr === '[object Object]') {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/wishes/create?id=${idStr}` })
}

onMounted(() => {
  wishStore.fetchWishes()
})

// 下拉刷新
onPullDownRefresh(() => {
  wishStore.fetchWishes().finally(() => {
    uni.stopPullDownRefresh()
  })
})

// 触底加载更多
onReachBottom(() => {
  wishStore.loadMore()
})
</script>

<style lang="scss" scoped>
.wishes-page {
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

// 愿望卡片
.wish-card {
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
    height: 240rpx;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
  margin-bottom: 8rpx;
}

.card-story {
  font-size: 24rpx;
  color: #666;
  line-height: 1.5;
  margin-bottom: 12rpx;
}

.card-footer {
  display: flex;
  align-items: center;
}

.card-status {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;

  &.active {
    background: #e8f5e9;
    color: #2e7d32;
  }

  &.achieved {
    background: #fff3e0;
    color: #e65100;
  }

  &.archived {
    background: #f5f5f5;
    color: #9e9e9e;
  }
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
  height: 240rpx;
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
