<template>
  <view class="notifications-page">
    <!-- 顶部标题栏 -->
    <view class="page-header">
      <text class="page-title">通知中心</text>
      <text class="mark-all-btn" v-if="notificationStore.unreadCount > 0" @click="markAllRead">
        全部已读
      </text>
    </view>

    <!-- 分类筛选 -->
    <view class="filter-tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        class="filter-tab"
        :class="{ active: currentTab === tab.value }"
        @click="switchTab(tab.value)"
      >
        <text class="tab-text">{{ tab.label }}</text>
      </view>
    </view>

    <!-- 通知列表 -->
    <view class="notification-list" v-if="filteredNotifications.length > 0">
      <view
        v-for="item in filteredNotifications"
        :key="item.id"
        class="notification-item"
        :class="{ unread: !item.is_read }"
        @click="handleNotificationClick(item)"
      >
        <view class="notification-icon">
          <text class="icon-emoji">{{ getTypeEmoji(item.type) }}</text>
          <view class="unread-dot" v-if="!item.is_read"></view>
        </view>
        <view class="notification-content">
          <text class="notification-title">{{ item.title }}</text>
          <text class="notification-desc">{{ item.content }}</text>
          <text class="notification-time">{{ formatTime(item.created_at) }}</text>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view class="empty-state" v-else-if="!notificationStore.loading">
      <text class="empty-emoji">🔔</text>
      <text class="empty-text">暂无通知</text>
    </view>

    <!-- 加载中 -->
    <view class="loading-state" v-if="notificationStore.loading">
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useNotificationStore } from '@/stores/notification'
import type { NotificationItem, NotificationType } from '@/stores/notification'

const notificationStore = useNotificationStore()

const currentTab = ref<string>('all')

const tabs = [
  { label: '全部', value: 'all' },
  { label: '任务', value: 'task_remind' },
  { label: '审核', value: 'review' },
  { label: '积分', value: 'points' },
  { label: '纪念日', value: 'anniversary' },
  { label: '系统', value: 'system' },
]

const filteredNotifications = computed(() => {
  if (currentTab.value === 'all') {
    return notificationStore.notifications
  }
  return notificationStore.notifications.filter(n => n.type === currentTab.value)
})

function switchTab(tab: string) {
  currentTab.value = tab
  const type = tab === 'all' ? undefined : tab as NotificationType
  notificationStore.fetchNotifications(type)
}

function getTypeEmoji(type: string): string {
  const map: Record<string, string> = {
    task_remind: '✅',
    review: '📋',
    points: '⭐',
    anniversary: '🎉',
    system: '🔔',
  }
  return map[type] || '📌'
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

function handleNotificationClick(item: NotificationItem) {
  // 标记已读
  if (!item.is_read) {
    notificationStore.markAsRead(item.id)
  }
  // 根据类型跳转
  navigateByType(item)
}

function navigateByType(item: NotificationItem) {
  const targetId = item.target_id
  switch (item.target_type) {
    case 'task':
      uni.navigateTo({ url: `/pages/tasks/detail?id=${targetId}` })
      break
    case 'review':
      uni.navigateTo({ url: '/pages/reviews/index' })
      break
    case 'points':
      uni.navigateTo({ url: '/pages/points/index' })
      break
    case 'wish':
      uni.navigateTo({ url: `/pages/wishes/detail?id=${targetId}` })
      break
    case 'goal':
      uni.navigateTo({ url: `/pages/goals/detail?id=${targetId}` })
      break
    default:
      // No navigation for system notifications
      break
  }
}

function markAllRead() {
  notificationStore.markAllAsRead()
}

onShow(() => {
  notificationStore.fetchNotifications()
})
</script>

<style lang="scss" scoped>
.notifications-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  background: #fff;
}

.page-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #1a1a2e;
}

.mark-all-btn {
  font-size: 26rpx;
  color: #4A90D9;
}

.filter-tabs {
  display: flex;
  padding: 16rpx 24rpx;
  background: #fff;
  gap: 16rpx;
  overflow-x: auto;
  border-bottom: 1rpx solid #f0f0f0;
}

.filter-tab {
  padding: 12rpx 24rpx;
  border-radius: 32rpx;
  background: #f5f6fa;
  white-space: nowrap;

  &.active {
    background: #4A90D9;
  }
}

.tab-text {
  font-size: 24rpx;
  color: #666;

  .active & {
    color: #fff;
  }
}

.notification-list {
  padding: 16rpx 24rpx;
}

.notification-item {
  display: flex;
  padding: 24rpx;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);

  &.unread {
    background: #f8faff;
    border-left: 4rpx solid #4A90D9;
  }
}

.notification-icon {
  position: relative;
  margin-right: 20rpx;
}

.icon-emoji {
  font-size: 40rpx;
}

.unread-dot {
  position: absolute;
  top: -4rpx;
  right: -4rpx;
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #FF4D4F;
}

.notification-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.notification-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #1a1a2e;
}

.notification-desc {
  font-size: 24rpx;
  color: #666;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 22rpx;
  color: #bbb;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.empty-emoji {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 48rpx;
}

.loading-text {
  font-size: 26rpx;
  color: #999;
}
</style>
