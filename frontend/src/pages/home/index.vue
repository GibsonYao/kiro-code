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
      <view class="stat-card" @click="goTo('/pages/wishes/index')">
        <text class="stat-number">{{ stats.wishes }}</text>
        <text class="stat-label">愿望</text>
      </view>
      <view class="stat-card" @click="goTo('/pages/goals/index')">
        <text class="stat-number">{{ stats.goals }}</text>
        <text class="stat-label">目标</text>
      </view>
      <view class="stat-card" @click="goTo('/pages/tasks/index')">
        <text class="stat-number">{{ stats.tasks }}</text>
        <text class="stat-label">任务</text>
      </view>
      <view class="stat-card">
        <text class="stat-number">{{ stats.completed }}</text>
        <text class="stat-label">已完成</text>
      </view>
    </view>

    <!-- 快速入口 -->
    <view class="quick-entries">
      <view class="quick-entry" @click="goTo('/pages/wishes/create')">
        <view class="quick-entry-icon wish-bg">
          <text class="quick-entry-emoji">💫</text>
        </view>
        <text class="quick-entry-label">许愿</text>
      </view>
      <view class="quick-entry" @click="goTo('/pages/goals/create')">
        <view class="quick-entry-icon goal-bg">
          <text class="quick-entry-emoji">🎯</text>
        </view>
        <text class="quick-entry-label">目标</text>
      </view>
      <view class="quick-entry" @click="goTo('/pages/tasks/create')">
        <view class="quick-entry-icon task-bg">
          <text class="quick-entry-emoji">✅</text>
        </view>
        <text class="quick-entry-label">任务</text>
      </view>
      <view class="quick-entry" @click="goTo('/pages/calendar/index')">
        <view class="quick-entry-icon calendar-bg">
          <text class="quick-entry-emoji">📅</text>
        </view>
        <text class="quick-entry-label">日历</text>
      </view>
    </view>

    <!-- 瀑布流混合内容区 -->
    <view class="section" v-if="feedItems.length > 0">
      <view class="section-header">
        <text class="section-title">📋 最近动态</text>
      </view>
      <view class="waterfall-container">
        <view class="waterfall-column waterfall-left">
          <view
            v-for="item in leftColumnItems"
            :key="item.id"
            class="waterfall-card"
            @click="goToDetail(item)"
          >
            <view class="card-cover" :style="{ background: getItemGradient(item) }">
              <image
                v-if="item.coverImage"
                :src="item.coverImage"
                class="card-cover-img"
                mode="aspectFill"
              />
              <view v-else class="card-cover-placeholder">
                <text class="card-cover-emoji">{{ getItemEmoji(item) }}</text>
              </view>
              <view class="card-type-badge" :class="item.type">
                <text class="card-type-text">{{ getTypeLabel(item.type) }}</text>
              </view>
            </view>
            <view class="card-body">
              <text class="card-title">{{ item.title }}</text>
              <text class="card-desc" v-if="item.description">{{ item.description }}</text>
              <view class="card-footer">
                <view class="card-status" :class="item.status">
                  <text class="card-status-text">{{ getStatusLabel(item) }}</text>
                </view>
                <text class="card-time">{{ formatTime(item.createdAt) }}</text>
              </view>
            </view>
          </view>
        </view>
        <view class="waterfall-column waterfall-right">
          <view
            v-for="item in rightColumnItems"
            :key="item.id"
            class="waterfall-card"
            @click="goToDetail(item)"
          >
            <view class="card-cover" :style="{ background: getItemGradient(item) }">
              <image
                v-if="item.coverImage"
                :src="item.coverImage"
                class="card-cover-img"
                mode="aspectFill"
              />
              <view v-else class="card-cover-placeholder">
                <text class="card-cover-emoji">{{ getItemEmoji(item) }}</text>
              </view>
              <view class="card-type-badge" :class="item.type">
                <text class="card-type-text">{{ getTypeLabel(item.type) }}</text>
              </view>
            </view>
            <view class="card-body">
              <text class="card-title">{{ item.title }}</text>
              <text class="card-desc" v-if="item.description">{{ item.description }}</text>
              <view class="card-footer">
                <view class="card-status" :class="item.status">
                  <text class="card-status-text">{{ getStatusLabel(item) }}</text>
                </view>
                <text class="card-time">{{ formatTime(item.createdAt) }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 空状态引导 -->
    <view class="section" v-else-if="!loading">
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
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useWishStore } from '@/stores/wish'
import { useGoalStore } from '@/stores/goal'
import { useTaskStore } from '@/stores/task'
import { checkAuth } from '@/utils/route-guard'
import type { WishItem, GoalItem, TaskItem } from '@/services/types'

const userStore = useUserStore()
const wishStore = useWishStore()
const goalStore = useGoalStore()
const taskStore = useTaskStore()

// Loading state
const loading = ref(false)

// FAB state
const fabOpen = ref(false)

// Stats
const stats = reactive({
  wishes: 0,
  goals: 0,
  tasks: 0,
  completed: 0,
})

// Feed item type for waterfall
interface FeedItem {
  id: string
  type: 'wish' | 'goal' | 'task'
  title: string
  description: string | null
  coverImage: string | null
  status: string
  createdAt: string
}

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

// Build mixed feed from wishes, goals, and tasks
const feedItems = computed<FeedItem[]>(() => {
  const items: FeedItem[] = []

  // Add wishes
  wishStore.wishes.slice(0, 6).forEach((wish: WishItem) => {
    items.push({
      id: `wish-${wish.id}`,
      type: 'wish',
      title: wish.display_text || wish.title,
      description: wish.vision_story ? wish.vision_story.slice(0, 60) : null,
      coverImage: wish.vision_image_url || wish.cover_image_url,
      status: wish.status,
      createdAt: wish.created_at,
    })
  })

  // Add goals
  goalStore.goals.slice(0, 6).forEach((goal: GoalItem) => {
    items.push({
      id: `goal-${goal.id}`,
      type: 'goal',
      title: goal.display_text || goal.title,
      description: goal.description ? goal.description.slice(0, 60) : null,
      coverImage: goal.cover_image_url,
      status: goal.status,
      createdAt: goal.created_at,
    })
  })

  // Add tasks
  taskStore.myTasks.slice(0, 6).forEach((task: TaskItem) => {
    items.push({
      id: `task-${task.id}`,
      type: 'task',
      title: task.display_text || task.title,
      description: task.description ? task.description.slice(0, 60) : null,
      coverImage: task.cover_image_url,
      status: task.status,
      createdAt: task.created_at,
    })
  })

  // Sort by creation time (newest first)
  items.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

  // Limit to 12 items for the feed
  return items.slice(0, 12)
})

// Split items into two columns for waterfall layout
const leftColumnItems = computed(() => {
  return feedItems.value.filter((_, index) => index % 2 === 0)
})

const rightColumnItems = computed(() => {
  return feedItems.value.filter((_, index) => index % 2 === 1)
})

// Gradient colors for cards without cover images
const cardGradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
]

function getItemGradient(item: FeedItem): string {
  if (item.coverImage) return 'transparent'
  const hash = item.id.charCodeAt(0) + item.id.charCodeAt(item.id.length - 1)
  return cardGradients[hash % cardGradients.length]
}

function getItemEmoji(item: FeedItem): string {
  const emojiMap: Record<string, string> = {
    wish: '💫',
    goal: '🎯',
    task: '✅',
  }
  return emojiMap[item.type] || '📌'
}

function getTypeLabel(type: string): string {
  const map: Record<string, string> = {
    wish: '愿望',
    goal: '目标',
    task: '任务',
  }
  return map[type] || type
}

function getStatusLabel(item: FeedItem): string {
  const wishStatusMap: Record<string, string> = {
    active: '进行中',
    achieved: '已实现',
    archived: '已归档',
  }
  const goalStatusMap: Record<string, string> = {
    active: '进行中',
    completed: '已完成',
    archived: '已归档',
  }
  const taskStatusMap: Record<string, string> = {
    pending: '待开始',
    claimed: '已认领',
    in_progress: '进行中',
    submitted: '待审核',
    approved: '已完成',
    rejected: '已驳回',
    expired: '已过期',
  }

  if (item.type === 'wish') return wishStatusMap[item.status] || item.status
  if (item.type === 'goal') return goalStatusMap[item.status] || item.status
  if (item.type === 'task') return taskStatusMap[item.status] || item.status
  return item.status
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function goTo(url: string) {
  uni.navigateTo({ url })
}

function goToDetail(item: FeedItem) {
  const rawId = item.id.replace(/^(wish|goal|task)-/, '')
  if (item.type === 'wish') {
    uni.navigateTo({ url: `/pages/wishes/create?id=${rawId}` })
  } else if (item.type === 'goal') {
    uni.navigateTo({ url: `/pages/goals/create?id=${rawId}` })
  } else if (item.type === 'task') {
    uni.navigateTo({ url: `/pages/tasks/detail?id=${rawId}` })
  }
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

async function loadData() {
  loading.value = true
  try {
    await Promise.all([
      wishStore.fetchWishes(),
      goalStore.fetchGoals(),
      taskStore.fetchMyTasks(),
    ])
    loadStats()
  } finally {
    loading.value = false
  }
}

function loadStats() {
  stats.wishes = wishStore.total || wishStore.wishes.length
  stats.goals = goalStore.total || goalStore.goals.length
  stats.tasks = taskStore.myTotal || taskStore.myTasks.length
  stats.completed =
    wishStore.wishes.filter(w => w.status === 'achieved').length +
    goalStore.goals.filter(g => g.status === 'completed').length +
    taskStore.myTasks.filter(t => t.status === 'approved').length
}

onShow(() => {
  if (!checkAuth()) return
  loadData()
})

onPullDownRefresh(async () => {
  await loadData()
  uni.stopPullDownRefresh()
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

// Quick entries
.quick-entries {
  display: flex;
  justify-content: space-around;
  padding: 24rpx 32rpx;
  margin: 0 24rpx 24rpx;
  background: #fff;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.quick-entry {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.quick-entry-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.wish-bg { background: linear-gradient(135deg, #f0e6ff 0%, #e8d5ff 100%); }
  &.goal-bg { background: linear-gradient(135deg, #e6f7ff 0%, #d5eeff 100%); }
  &.task-bg { background: linear-gradient(135deg, #e6ffe6 0%, #d5ffd5 100%); }
  &.calendar-bg { background: linear-gradient(135deg, #fff7e6 0%, #ffeed5 100%); }
}

.quick-entry-emoji {
  font-size: 36rpx;
}

.quick-entry-label {
  font-size: 22rpx;
  color: #666;
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

// Waterfall layout
.waterfall-container {
  display: flex;
  gap: 16rpx;
}

.waterfall-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.waterfall-card {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
  transition: transform 0.2s;

  &:active {
    transform: scale(0.97);
  }
}

.card-cover {
  position: relative;
  min-height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-cover-img {
  width: 100%;
  height: 200rpx;
  display: block;
}

.card-cover-placeholder {
  width: 100%;
  height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-cover-emoji {
  font-size: 56rpx;
}

.card-type-badge {
  position: absolute;
  top: 12rpx;
  left: 12rpx;
  padding: 4rpx 14rpx;
  border-radius: 16rpx;
  backdrop-filter: blur(4px);

  &.wish {
    background: rgba(102, 126, 234, 0.85);
  }
  &.goal {
    background: rgba(79, 172, 254, 0.85);
  }
  &.task {
    background: rgba(67, 233, 123, 0.85);
  }
}

.card-type-text {
  font-size: 20rpx;
  color: #fff;
  font-weight: 500;
}

.card-body {
  padding: 16rpx 20rpx 20rpx;
}

.card-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #1a1a2e;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
  margin-bottom: 8rpx;
}

.card-desc {
  font-size: 22rpx;
  color: #888;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
  margin-bottom: 12rpx;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-status {
  padding: 4rpx 12rpx;
  border-radius: 12rpx;

  &.active {
    background: #e8f5e9;
  }
  &.achieved, &.completed, &.approved {
    background: #fff3e0;
  }
  &.archived {
    background: #f5f5f5;
  }
  &.pending, &.claimed {
    background: #e3f2fd;
  }
  &.in_progress {
    background: #e8f5e9;
  }
  &.submitted {
    background: #fce4ec;
  }
  &.rejected {
    background: #ffebee;
  }
  &.expired {
    background: #f5f5f5;
  }
}

.card-status-text {
  font-size: 20rpx;
  color: #555;
}

.card-time {
  font-size: 20rpx;
  color: #bbb;
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
