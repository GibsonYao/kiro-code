<template>
  <view class="home-page">
    <!-- 顶部问候区域 -->
    <view class="hero-section">
      <view class="hero-content">
        <text class="greeting-emoji">{{ greetingEmoji }}</text>
        <text class="greeting-text">{{ greeting }}</text>
        <text class="motivational-text">{{ motivationalQuote }}</text>
      </view>
    </view>

    <!-- 进度统计 -->
    <view class="stats-section">
      <view class="stat-card">
        <text class="stat-number">{{ stats.wishes }}</text>
        <text class="stat-label">愿望</text>
      </view>
      <view class="stat-card">
        <text class="stat-number">{{ stats.goals }}</text>
        <text class="stat-label">目标</text>
      </view>
      <view class="stat-card">
        <text class="stat-number">{{ stats.tasks }}</text>
        <text class="stat-label">任务</text>
      </view>
      <view class="stat-card">
        <text class="stat-number">{{ stats.completed }}</text>
        <text class="stat-label">已完成</text>
      </view>
    </view>

    <!-- 最近愿望 -->
    <view class="section" v-if="recentWishes.length > 0">
      <view class="section-header">
        <text class="section-title">✨ 我的愿望</text>
        <text class="section-more" @click="goTo('/pages/wishes/index')">查看全部</text>
      </view>
      <scroll-view class="wish-scroll" scroll-x :show-scrollbar="false">
        <view class="wish-cards-row">
          <view
            v-for="wish in recentWishes"
            :key="wish.id"
            class="wish-visual-card"
            @click="goToWishDetail(wish.id)"
          >
            <view class="wish-card-bg" :style="{ background: getCardGradient(wish) }">
              <text class="wish-card-emoji">💫</text>
            </view>
            <view class="wish-card-body">
              <text class="wish-card-title">{{ wish.display_text || wish.title }}</text>
              <text class="wish-card-status" :class="wish.status">
                {{ statusLabel(wish.status) }}
              </text>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 空状态引导 -->
    <view class="section" v-else>
      <view class="empty-inspire">
        <text class="empty-inspire-emoji">🌟</text>
        <text class="empty-inspire-title">开始你的第一个愿望</text>
        <text class="empty-inspire-desc">从一个小小的愿望开始，AI会帮你拆解成可执行的目标和任务</text>
        <view class="empty-inspire-btn" @click="goTo('/pages/wishes/create')">
          <text class="empty-inspire-btn-text">创建愿望</text>
        </view>
      </view>
    </view>

    <!-- 目标管理链路 -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">🚀 目标管理链路</text>
      </view>
      <view class="chain-card">
        <view class="chain-flow">
          <view class="chain-step" @click="goTo('/pages/wishes/index')">
            <view class="chain-icon-wrap wish-bg">
              <text class="chain-emoji">💫</text>
            </view>
            <text class="chain-name">愿望</text>
          </view>
          <view class="chain-arrow-wrap">
            <text class="chain-arrow">→</text>
          </view>
          <view class="chain-step" @click="goTo('/pages/goals/index')">
            <view class="chain-icon-wrap goal-bg">
              <text class="chain-emoji">🎯</text>
            </view>
            <text class="chain-name">目标</text>
          </view>
          <view class="chain-arrow-wrap">
            <text class="chain-arrow">→</text>
          </view>
          <view class="chain-step" @click="goTo('/pages/plans/index')">
            <view class="chain-icon-wrap plan-bg">
              <text class="chain-emoji">📋</text>
            </view>
            <text class="chain-name">计划</text>
          </view>
          <view class="chain-arrow-wrap">
            <text class="chain-arrow">→</text>
          </view>
          <view class="chain-step" @click="goTo('/pages/tasks/index')">
            <view class="chain-icon-wrap task-bg">
              <text class="chain-emoji">✅</text>
            </view>
            <text class="chain-name">任务</text>
          </view>
          <view class="chain-arrow-wrap">
            <text class="chain-arrow">→</text>
          </view>
          <view class="chain-step" @click="goTo('/pages/actions/index')">
            <view class="chain-icon-wrap action-bg">
              <text class="chain-emoji">⚡</text>
            </view>
            <text class="chain-name">行动</text>
          </view>
        </view>
        <text class="chain-desc">从愿望出发，AI帮你逐步拆解为可执行的行动</text>
      </view>
    </view>

    <!-- 底部安全区 -->
    <view class="safe-bottom"></view>

    <!-- FAB 浮动操作按钮 -->
    <view class="fab-overlay" v-if="fabOpen" @click="closeFab"></view>
    <view class="fab-menu" v-if="fabOpen">
      <view class="fab-item" @click="fabAction('/pages/wishes/create')">
        <text class="fab-item-icon">💫</text>
        <text class="fab-item-label">新愿望</text>
      </view>
      <view class="fab-item" @click="fabAction('/pages/goals/create')">
        <text class="fab-item-icon">🎯</text>
        <text class="fab-item-label">新目标</text>
      </view>
      <view class="fab-item" @click="fabAction('/pages/plans/create')">
        <text class="fab-item-icon">📋</text>
        <text class="fab-item-label">新计划</text>
      </view>
      <view class="fab-item" @click="fabAction('/pages/tasks/create')">
        <text class="fab-item-icon">✅</text>
        <text class="fab-item-label">新任务</text>
      </view>
      <view class="fab-item" @click="fabAction('/pages/actions/create')">
        <text class="fab-item-icon">⚡</text>
        <text class="fab-item-label">新行动</text>
      </view>
    </view>
    <view class="fab-btn" :class="{ active: fabOpen }" @click="toggleFab">
      <text class="fab-icon">{{ fabOpen ? '✕' : '+' }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useWishStore } from '@/stores/wish'
import { checkAuth } from '@/utils/route-guard'
import type { WishStatus } from '@/services/types'

const userStore = useUserStore()
const wishStore = useWishStore()

// FAB state
const fabOpen = ref(false)

// Stats
const stats = reactive({
  wishes: 0,
  goals: 0,
  tasks: 0,
  completed: 0,
})

const greetingEmoji = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '🌙'
  if (hour < 12) return '🌅'
  if (hour < 18) return '☀️'
  return '🌆'
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  const name = userStore.nickname || '家人'
  if (hour < 6) return `夜深了，${name}`
  if (hour < 12) return `早上好，${name}`
  if (hour < 18) return `下午好，${name}`
  return `晚上好，${name}`
})

const motivationalQuotes = [
  '每一个伟大的目标，都始于一个小小的愿望 🌱',
  '今天的行动，是明天成就的种子 🌟',
  '把大梦想拆解成小步骤，一步步实现 🚀',
  '坚持每天进步一点点，终将遇见更好的自己 ✨',
  '不要等待完美时机，现在就是最好的开始 💪',
]

const motivationalQuote = computed(() => {
  const dayIndex = new Date().getDate() % motivationalQuotes.length
  return motivationalQuotes[dayIndex]
})

const recentWishes = computed(() => {
  return wishStore.wishes.slice(0, 5)
})

const cardGradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
]

function getCardGradient(wish: { id: string }): string {
  const hash = wish.id.charCodeAt(0) + wish.id.charCodeAt(wish.id.length - 1)
  return cardGradients[hash % cardGradients.length]
}

function statusLabel(status: WishStatus): string {
  const map: Record<WishStatus, string> = {
    active: '进行中',
    achieved: '已实现',
    archived: '已归档',
  }
  return map[status] || status
}

function goTo(url: string) {
  uni.navigateTo({ url })
}

function goToWishDetail(id: string) {
  const idStr = String(id)
  uni.navigateTo({ url: `/pages/wishes/create?id=${idStr}` })
}

function toggleFab() {
  fabOpen.value = !fabOpen.value
}

function closeFab() {
  fabOpen.value = false
}

function fabAction(url: string) {
  fabOpen.value = false
  uni.navigateTo({ url })
}

async function loadStats() {
  // Use wish store data for stats
  stats.wishes = wishStore.total || wishStore.wishes.length
  // For goals/tasks/completed, we'd need separate API calls
  // For now, show wish-based stats
  stats.goals = 0
  stats.tasks = 0
  stats.completed = wishStore.wishes.filter(w => w.status === 'achieved').length

  // Try to fetch goals/tasks counts from API
  try {
    const { get } = await import('@/services/request')
    const goalsRes = await get<{ total: number }>('/goals', { page: 1, page_size: 1 })
    if (goalsRes && typeof goalsRes === 'object' && 'total' in goalsRes) {
      stats.goals = goalsRes.total
    }
  } catch {
    // Silently fail - stats are optional
  }

  try {
    const { get } = await import('@/services/request')
    const tasksRes = await get<{ total: number; items: Array<{ status: string }> }>('/tasks', { page: 1, page_size: 100 })
    if (tasksRes && typeof tasksRes === 'object' && 'total' in tasksRes) {
      stats.tasks = tasksRes.total
      if ('items' in tasksRes && Array.isArray(tasksRes.items)) {
        stats.completed += tasksRes.items.filter((t) => t.status === 'approved').length
      }
    }
  } catch {
    // Silently fail
  }
}

onShow(() => {
  if (!checkAuth()) return
  wishStore.fetchWishes().then(() => {
    loadStats()
  })
})
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
  padding: 0 0 160rpx 0;
  background-color: #f5f6fa;
}

// Hero section
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60rpx 32rpx 48rpx;
  border-radius: 0 0 40rpx 40rpx;
}

.hero-content {
  display: flex;
  flex-direction: column;
}

.greeting-emoji {
  font-size: 56rpx;
  margin-bottom: 12rpx;
}

.greeting-text {
  font-size: 40rpx;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12rpx;
}

.motivational-text {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
}

// Stats section
.stats-section {
  display: flex;
  margin: -30rpx 24rpx 24rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx 16rpx;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 1;
}

.stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.stat-number {
  font-size: 40rpx;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 22rpx;
  color: #999;
}

// Section
.section {
  padding: 0 24rpx;
  margin-bottom: 32rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
  padding-top: 8rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1a1a2e;
}

.section-more {
  font-size: 24rpx;
  color: #667eea;
}

// Wish cards horizontal scroll
.wish-scroll {
  white-space: nowrap;
  width: 100%;
}

.wish-cards-row {
  display: inline-flex;
  gap: 20rpx;
  padding: 8rpx 0 16rpx;
}

.wish-visual-card {
  width: 260rpx;
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
  display: inline-block;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.96);
  }
}

.wish-card-bg {
  height: 140rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wish-card-emoji {
  font-size: 48rpx;
}

.wish-card-body {
  padding: 16rpx 20rpx 20rpx;
  white-space: normal;
}

.wish-card-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #1a1a2e;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8rpx;
  line-height: 1.4;
}

.wish-card-status {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 16rpx;

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

// Empty inspire
.empty-inspire {
  background: #fff;
  border-radius: 24rpx;
  padding: 48rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.empty-inspire-emoji {
  font-size: 64rpx;
  margin-bottom: 20rpx;
}

.empty-inspire-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 12rpx;
}

.empty-inspire-desc {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
  margin-bottom: 32rpx;
}

.empty-inspire-btn {
  padding: 20rpx 48rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 40rpx;
  box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.3);
}

.empty-inspire-btn-text {
  color: #fff;
  font-size: 28rpx;
  font-weight: 500;
}

// Chain card
.chain-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 32rpx 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.chain-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.chain-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.chain-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.wish-bg { background: #f0e6ff; }
  &.goal-bg { background: #e6f7ff; }
  &.plan-bg { background: #fff7e6; }
  &.task-bg { background: #e6ffe6; }
  &.action-bg { background: #fff0e6; }
}

.chain-emoji {
  font-size: 28rpx;
}

.chain-name {
  font-size: 20rpx;
  color: #666;
}

.chain-arrow-wrap {
  padding: 0 4rpx;
  margin-bottom: 24rpx;
}

.chain-arrow {
  font-size: 22rpx;
  color: #ccc;
}

.chain-desc {
  display: block;
  text-align: center;
  font-size: 24rpx;
  color: #999;
}

// Safe bottom
.safe-bottom {
  height: env(safe-area-inset-bottom);
}

// FAB - Floating Action Button
.fab-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 998;
  animation: fadeIn 0.2s ease;
}

.fab-menu {
  position: fixed;
  right: 32rpx;
  bottom: 180rpx;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  animation: slideUp 0.25s ease;
}

.fab-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  background: #fff;
  padding: 20rpx 28rpx;
  border-radius: 40rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.12);
  transition: transform 0.15s;

  &:active {
    transform: scale(0.95);
  }
}

.fab-item-icon {
  font-size: 32rpx;
}

.fab-item-label {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.fab-btn {
  position: fixed;
  right: 32rpx;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 32rpx rgba(102, 126, 234, 0.5);
  z-index: 1000;
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &.active {
    transform: rotate(0deg);
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    box-shadow: 0 8rpx 32rpx rgba(238, 90, 36, 0.5);
  }

  &:active {
    transform: scale(0.9);
  }
}

.fab-icon {
  font-size: 48rpx;
  color: #fff;
  font-weight: 300;
  line-height: 1;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
