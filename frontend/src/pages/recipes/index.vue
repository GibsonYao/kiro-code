<template>
  <view class="recipes-page">
    <!-- 页面标题栏 -->
    <view class="page-header">
      <text class="page-title">我的食谱</text>
      <view class="header-actions">
        <view class="pref-btn" @click="goPreferences">
          <text class="pref-icon">⚙️</text>
        </view>
        <view class="add-btn" @click="goCreate">
          <text class="add-icon">+</text>
        </view>
      </view>
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrap">
        <text class="search-icon">🔍</text>
        <input
          v-model="keyword"
          class="search-input"
          placeholder="搜索食谱..."
          confirm-type="search"
          @confirm="handleSearch"
        />
        <text v-if="keyword" class="clear-btn" @click="clearSearch">✕</text>
      </view>
    </view>

    <!-- 筛选标签 -->
    <view class="filter-row">
      <view
        class="filter-tag"
        :class="{ active: activeFilter === 'all' }"
        @click="setFilter('all')"
      >
        <text>全部</text>
      </view>
      <view
        class="filter-tag"
        :class="{ active: activeFilter === 'recent' }"
        @click="setFilter('recent')"
      >
        <text>最近添加</text>
      </view>
      <view
        class="filter-tag"
        :class="{ active: activeFilter === 'ai' }"
        @click="setFilter('ai')"
      >
        <text>AI推荐</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading && recipes.length === 0" class="loading-state">
      <view class="skeleton-card" v-for="i in 4" :key="i">
        <view class="skeleton-image"></view>
        <view class="skeleton-text"></view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="filteredRecipes.length === 0 && !loading" class="empty-state">
      <text class="empty-emoji">🍳</text>
      <text class="empty-text">{{ keyword ? '没有找到相关食谱' : '还没有食谱' }}</text>
      <text class="empty-hint">{{ keyword ? '换个关键词试试' : '点击右上角 + 添加家庭食谱' }}</text>
      <view v-if="!keyword" class="empty-btn" @click="goCreate">
        <text>添加食谱</text>
      </view>
    </view>

    <!-- 瀑布流食谱列表 -->
    <view v-else class="waterfall-grid">
      <view class="waterfall-column">
        <view
          v-for="recipe in leftColumn"
          :key="recipe.id"
          class="recipe-card"
          @click="goDetail(recipe.id)"
        >
          <image
            v-if="recipe.cover_image_url"
            :src="recipe.cover_image_url"
            class="recipe-cover"
            mode="widthFix"
          />
          <view v-else class="recipe-cover-placeholder">
            <text class="placeholder-emoji">{{ getRandomFoodEmoji(recipe.id) }}</text>
          </view>
          <view class="recipe-info">
            <text class="recipe-name">{{ recipe.name }}</text>
            <text v-if="recipe.description" class="recipe-desc">
              {{ recipe.description.slice(0, 30) }}{{ recipe.description.length > 30 ? '...' : '' }}
            </text>
            <view class="recipe-meta">
              <text v-if="recipe.ingredients" class="meta-item">
                🥬 {{ recipe.ingredients.length }}种食材
              </text>
            </view>
          </view>
        </view>
      </view>
      <view class="waterfall-column">
        <view
          v-for="recipe in rightColumn"
          :key="recipe.id"
          class="recipe-card"
          @click="goDetail(recipe.id)"
        >
          <image
            v-if="recipe.cover_image_url"
            :src="recipe.cover_image_url"
            class="recipe-cover"
            mode="widthFix"
          />
          <view v-else class="recipe-cover-placeholder">
            <text class="placeholder-emoji">{{ getRandomFoodEmoji(recipe.id) }}</text>
          </view>
          <view class="recipe-info">
            <text class="recipe-name">{{ recipe.name }}</text>
            <text v-if="recipe.description" class="recipe-desc">
              {{ recipe.description.slice(0, 30) }}{{ recipe.description.length > 30 ? '...' : '' }}
            </text>
            <view class="recipe-meta">
              <text v-if="recipe.steps" class="meta-item">
                📝 {{ recipe.steps.length }}步
              </text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 加载更多 -->
    <view v-if="hasMore" class="load-more" @click="loadMore">
      <text v-if="loading">加载中...</text>
      <text v-else>加载更多</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { recipeApi } from '@/services/api/recipes'
import { checkAuth } from '@/utils/route-guard'
import type { RecipeItem } from '@/services/types'

const recipes = ref<RecipeItem[]>([])
const loading = ref(false)
const hasMore = ref(false)
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const activeFilter = ref('all')

const foodEmojis = ['🍲', '🍜', '🍛', '🥘', '🍝', '🥗', '🍱', '🍣', '🥟', '🍕', '🌮', '🍔']

const filteredRecipes = computed(() => {
  let list = recipes.value
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase()
    list = list.filter(r =>
      r.name.toLowerCase().includes(kw) ||
      (r.description && r.description.toLowerCase().includes(kw))
    )
  }
  return list
})

const leftColumn = computed(() => {
  return filteredRecipes.value.filter((_, idx) => idx % 2 === 0)
})

const rightColumn = computed(() => {
  return filteredRecipes.value.filter((_, idx) => idx % 2 === 1)
})

function getRandomFoodEmoji(id: string): string {
  const hash = id.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
  return foodEmojis[hash % foodEmojis.length]
}

async function fetchRecipes() {
  loading.value = true
  try {
    page.value = 1
    const res = await recipeApi.getRecipes({ page: 1, page_size: pageSize })
    recipes.value = res.items
    hasMore.value = res.has_more
  } catch {
    recipes.value = []
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (!hasMore.value || loading.value) return
  loading.value = true
  try {
    const nextPage = page.value + 1
    const res = await recipeApi.getRecipes({ page: nextPage, page_size: pageSize })
    recipes.value = [...recipes.value, ...res.items]
    page.value = nextPage
    hasMore.value = res.has_more
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // Client-side filtering is already reactive via computed
}

function clearSearch() {
  keyword.value = ''
}

function setFilter(filter: string) {
  activeFilter.value = filter
}

function goCreate() {
  uni.navigateTo({ url: '/pages/recipes/create' })
}

function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/recipes/detail?id=${id}` })
}

function goPreferences() {
  uni.navigateTo({ url: '/pages/recipes/preferences' })
}

onMounted(() => {
  fetchRecipes()
})

onShow(() => {
  checkAuth()
  fetchRecipes()
})

onPullDownRefresh(() => {
  fetchRecipes().finally(() => uni.stopPullDownRefresh())
})

onReachBottom(() => {
  loadMore()
})
</script>

<style lang="scss" scoped>
.recipes-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding: 24rpx;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.page-title {
  font-size: 40rpx;
  font-weight: 700;
  color: #1a1a2e;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.pref-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.08);
}

.pref-icon {
  font-size: 32rpx;
}

.add-btn {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(240, 147, 251, 0.4);
}

.add-icon {
  font-size: 40rpx;
  color: #fff;
  font-weight: 300;
}

.search-bar {
  margin-bottom: 20rpx;
}

.search-input-wrap {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 40rpx;
  padding: 0 24rpx;
  height: 72rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.search-icon {
  font-size: 28rpx;
  margin-right: 12rpx;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.clear-btn {
  font-size: 28rpx;
  color: #999;
  padding: 8rpx;
}

.filter-row {
  display: flex;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.filter-tag {
  padding: 10rpx 24rpx;
  background: #fff;
  border-radius: 20rpx;
  font-size: 24rpx;
  color: #666;
  border: 1rpx solid #e8e8e8;

  &.active {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: #fff;
    border-color: transparent;
  }
}

.waterfall-grid {
  display: flex;
  gap: 16rpx;
}

.waterfall-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.recipe-card {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.recipe-cover {
  width: 100%;
  min-height: 200rpx;
}

.recipe-cover-placeholder {
  width: 100%;
  height: 240rpx;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-emoji {
  font-size: 72rpx;
}

.recipe-info {
  padding: 20rpx;
}

.recipe-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.recipe-desc {
  font-size: 22rpx;
  color: #666;
  display: block;
  margin-bottom: 8rpx;
}

.recipe-meta {
  display: flex;
  gap: 12rpx;
}

.meta-item {
  font-size: 20rpx;
  color: #999;
}

.loading-state {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.skeleton-card {
  width: calc(50% - 8rpx);
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
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
  margin: 16rpx;
  background: #f0f0f0;
  border-radius: 8rpx;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 160rpx;
}

.empty-emoji {
  font-size: 96rpx;
  margin-bottom: 24rpx;
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
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 40rpx;
  color: #fff;
  font-size: 28rpx;
}

.load-more {
  text-align: center;
  padding: 32rpx;
  color: #999;
  font-size: 26rpx;
}
</style>
