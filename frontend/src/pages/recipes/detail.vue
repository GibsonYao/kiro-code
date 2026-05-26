<template>
  <view class="recipe-detail-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">食谱详情</text>
      <view class="nav-right">
        <text class="edit-link" @click="goEdit">编辑</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <text>加载中...</text>
    </view>

    <scroll-view v-else-if="recipe" class="content" scroll-y>
      <!-- 封面图 -->
      <view class="cover-section">
        <image
          v-if="recipe.cover_image_url"
          :src="recipe.cover_image_url"
          class="cover-image"
          mode="aspectFill"
        />
        <view v-else class="cover-placeholder">
          <text class="cover-emoji">{{ getRandomFoodEmoji() }}</text>
        </view>
      </view>

      <!-- 基本信息 -->
      <view class="info-section">
        <text class="recipe-name">{{ recipe.name }}</text>
        <text v-if="recipe.description" class="recipe-desc">{{ recipe.description }}</text>
        <view class="recipe-stats">
          <view class="stat-item">
            <text class="stat-value">{{ recipe.ingredients?.length || 0 }}</text>
            <text class="stat-label">种食材</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item">
            <text class="stat-value">{{ recipe.steps?.length || 0 }}</text>
            <text class="stat-label">个步骤</text>
          </view>
        </view>
      </view>

      <!-- 食材清单 -->
      <view class="section-card">
        <view class="section-header">
          <text class="section-icon">🥬</text>
          <text class="section-title">食材清单</text>
        </view>
        <view v-if="recipe.ingredients && recipe.ingredients.length > 0" class="ingredients-list">
          <view
            v-for="(item, idx) in recipe.ingredients"
            :key="idx"
            class="ingredient-item"
          >
            <view class="ingredient-dot"></view>
            <text class="ingredient-text">{{ item }}</text>
          </view>
        </view>
        <view v-else class="empty-section">
          <text class="empty-section-text">暂无食材信息</text>
        </view>
      </view>

      <!-- 做法步骤 -->
      <view class="section-card">
        <view class="section-header">
          <text class="section-icon">📝</text>
          <text class="section-title">做法步骤</text>
        </view>
        <view v-if="recipe.steps && recipe.steps.length > 0" class="steps-list">
          <view
            v-for="(step, idx) in recipe.steps"
            :key="idx"
            class="step-item"
          >
            <view class="step-number">
              <text class="step-num-text">{{ idx + 1 }}</text>
            </view>
            <text class="step-text">{{ step }}</text>
          </view>
        </view>
        <view v-else class="empty-section">
          <text class="empty-section-text">暂无步骤信息</text>
        </view>
      </view>

      <!-- 底部间距 -->
      <view class="bottom-spacer"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { recipeApi } from '@/services/api/recipes'
import type { RecipeItem } from '@/services/types'

const recipe = ref<RecipeItem | null>(null)
const loading = ref(false)
const recipeId = ref('')

const foodEmojis = ['🍲', '🍜', '🍛', '🥘', '🍝', '🥗', '🍱', '🍣', '🥟', '🍕']

onLoad((query) => {
  if (query?.id) {
    recipeId.value = query.id
    loadRecipe(query.id)
  }
})

async function loadRecipe(id: string) {
  loading.value = true
  try {
    recipe.value = await recipeApi.getRecipe(id)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function getRandomFoodEmoji(): string {
  return foodEmojis[Math.floor(Math.random() * foodEmojis.length)]
}

function goBack() {
  uni.navigateBack()
}

function goEdit() {
  uni.navigateTo({ url: `/pages/recipes/create?id=${recipeId.value}` })
}
</script>

<style lang="scss" scoped>
.recipe-detail-page {
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
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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

.edit-link {
  font-size: 28rpx;
  color: #fff;
}

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 28rpx;
}

.content {
  flex: 1;
}

.cover-section {
  width: 100%;
}

.cover-image {
  width: 100%;
  height: 400rpx;
}

.cover-placeholder {
  width: 100%;
  height: 400rpx;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-emoji {
  font-size: 120rpx;
}

.info-section {
  background: #fff;
  padding: 32rpx;
  margin-bottom: 16rpx;
}

.recipe-name {
  font-size: 36rpx;
  font-weight: 700;
  color: #1a1a2e;
  display: block;
  margin-bottom: 12rpx;
}

.recipe-desc {
  font-size: 28rpx;
  color: #666;
  display: block;
  margin-bottom: 24rpx;
  line-height: 1.6;
}

.recipe-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 48rpx;
}

.stat-value {
  font-size: 36rpx;
  font-weight: 700;
  color: #f5576c;
}

.stat-label {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
}

.stat-divider {
  width: 1rpx;
  height: 48rpx;
  background: #e8e8e8;
}

.section-card {
  background: #fff;
  margin: 0 0 16rpx;
  padding: 32rpx;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.section-icon {
  font-size: 36rpx;
  margin-right: 12rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.ingredients-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.ingredient-item {
  display: flex;
  align-items: center;
  padding: 16rpx 20rpx;
  background: #f9f9fb;
  border-radius: 8rpx;
}

.ingredient-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #52c41a;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.ingredient-text {
  font-size: 28rpx;
  color: #333;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.step-item {
  display: flex;
  align-items: flex-start;
}

.step-number {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 16rpx;
  margin-top: 4rpx;
}

.step-num-text {
  font-size: 24rpx;
  color: #fff;
  font-weight: 600;
}

.step-text {
  flex: 1;
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
}

.empty-section {
  padding: 32rpx;
  text-align: center;
}

.empty-section-text {
  font-size: 26rpx;
  color: #999;
}

.bottom-spacer {
  height: 48rpx;
}
</style>
