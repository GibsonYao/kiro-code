<template>
  <view class="wish-detail-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">愿望详情</text>
      <view class="nav-right" />
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 愿望内容 -->
    <scroll-view v-else-if="wish" class="detail-content" scroll-y>
      <!-- 愿景图片 -->
      <image
        v-if="wish.vision_image_url"
        :src="wish.vision_image_url"
        class="vision-image"
        mode="aspectFill"
      />
      <view v-else class="vision-placeholder">
        <text class="placeholder-icon">✨</text>
        <text class="placeholder-text">愿景图片生成中...</text>
      </view>

      <!-- 愿景故事 -->
      <view class="story-section" v-if="wish.vision_story">
        <text class="section-title">愿景故事</text>
        <text class="story-text">{{ wish.vision_story }}</text>
      </view>

      <!-- 基本信息 -->
      <view class="info-section">
        <text class="wish-title">{{ wish.title }}</text>
        <view class="status-row">
          <view class="status-badge" :class="'status-' + wish.status">
            {{ statusLabel(wish.status) }}
          </view>
        </view>
        <text v-if="wish.display_text" class="display-text">{{ wish.display_text }}</text>
      </view>

      <!-- 重新生成按钮 -->
      <view class="action-section">
        <button class="regenerate-btn" :disabled="regenerating" @click="handleRegenerate">
          {{ regenerating ? '生成中...' : '🔄 重新生成' }}
        </button>
      </view>

      <!-- 关联目标 -->
      <view class="section">
        <text class="section-title">关联目标</text>
        <view v-if="relatedGoals.length > 0" class="goals-list">
          <view
            v-for="goal in relatedGoals"
            :key="goal.id"
            class="goal-card"
            @click="goGoalDetail(goal.id)"
          >
            <view class="goal-info">
              <text class="goal-title">{{ goal.title }}</text>
              <view class="goal-progress-bar">
                <view class="goal-progress-fill" :style="{ width: goal.progress + '%' }" />
              </view>
            </view>
            <text class="goal-arrow">›</text>
          </view>
        </view>
        <view v-else class="empty-state">
          <text class="empty-text">暂无关联目标</text>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { wishApi } from '@/services/api/wishes'
import { goalApi } from '@/services/api/goals'
import type { WishItem, GoalItem } from '@/services/types'

const wish = ref<WishItem | null>(null)
const relatedGoals = ref<GoalItem[]>([])
const loading = ref(true)
const regenerating = ref(false)

onLoad((query) => {
  const id = query?.id
  if (id) {
    loadWish(id)
    loadRelatedGoals(id)
  }
})

async function loadWish(id: string) {
  loading.value = true
  try {
    wish.value = await wishApi.getWish(id)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadRelatedGoals(wishId: string) {
  try {
    const res = await goalApi.getGoals({ page: 1, page_size: 50 })
    // Filter goals that belong to this wish
    relatedGoals.value = res.items.filter(g => g.wish_id === wishId)
  } catch {
    // Silently fail for related goals
  }
}

async function handleRegenerate() {
  if (!wish.value) return
  regenerating.value = true
  try {
    wish.value = await wishApi.regenerateVision(wish.value.id)
    uni.showToast({ title: '已重新生成', icon: 'success' })
  } catch {
    uni.showToast({ title: '生成失败', icon: 'none' })
  } finally {
    regenerating.value = false
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    active: '进行中',
    achieved: '已实现',
    archived: '已归档',
  }
  return map[status] || status
}

function goGoalDetail(id: string) {
  uni.navigateTo({ url: `/pages/goals/detail?id=${id}` })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.wish-detail-page {
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

.vision-image {
  width: 100%;
  height: 480rpx;
}

.vision-placeholder {
  width: 100%;
  height: 480rpx;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  font-size: 80rpx;
  margin-bottom: 16rpx;
}

.placeholder-text {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
}

.story-section {
  background: #fff;
  padding: 32rpx;
  margin-bottom: 16rpx;
}

.story-text {
  font-size: 28rpx;
  color: #555;
  line-height: 1.8;
  display: block;
}

.info-section {
  background: #fff;
  padding: 32rpx;
  margin-bottom: 16rpx;
}

.wish-title {
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
  &.status-achieved {
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
  color: #666;
  line-height: 1.6;
  display: block;
}

.action-section {
  padding: 0 32rpx 16rpx;
}

.regenerate-btn {
  width: 100%;
  height: 80rpx;
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: #fff;
  font-size: 28rpx;
  font-weight: 600;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &[disabled] {
    opacity: 0.6;
  }
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

.goals-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.goal-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.goal-info {
  flex: 1;
}

.goal-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  display: block;
  margin-bottom: 12rpx;
}

.goal-progress-bar {
  height: 8rpx;
  background: #e8e8e8;
  border-radius: 4rpx;
  overflow: hidden;
}

.goal-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4rpx;
  transition: width 0.3s;
}

.goal-arrow {
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
