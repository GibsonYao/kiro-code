<template>
  <view class="notification-badge-wrap" @click="goToNotifications">
    <text class="badge-icon">🔔</text>
    <view class="badge-count" v-if="notificationStore.unreadCount > 0">
      <text class="badge-count-text">
        {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

function goToNotifications() {
  uni.navigateTo({ url: '/pages/notifications/index' })
}
</script>

<style lang="scss" scoped>
.notification-badge-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.badge-icon {
  font-size: 40rpx;
}

.badge-count {
  position: absolute;
  top: 0;
  right: 0;
  min-width: 32rpx;
  height: 32rpx;
  padding: 0 8rpx;
  border-radius: 16rpx;
  background: #FF4D4F;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-count-text {
  font-size: 18rpx;
  color: #fff;
  font-weight: 600;
}
</style>
