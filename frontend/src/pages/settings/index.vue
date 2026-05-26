<template>
  <view class="settings-page">
    <view class="section">
      <view class="menu-list">
        <view class="menu-item" @click="goTo('/pages/profile/edit')">
          <text class="menu-text">个人信息</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/notifications/index')">
          <text class="menu-text">消息通知</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item">
          <text class="menu-text">深色模式</text>
          <switch :checked="isDarkMode" @change="toggleDarkMode" color="#4A90D9" />
        </view>
        <view class="menu-item">
          <text class="menu-text">隐私设置</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item">
          <text class="menu-text">关于我们</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const isDarkMode = ref(uni.getStorageSync('darkMode') === 'true')

function goTo(url: string) {
  uni.navigateTo({ url })
}

function toggleDarkMode(e: { detail: { value: boolean } }) {
  isDarkMode.value = e.detail.value
  uni.setStorageSync('darkMode', String(isDarkMode.value))

  // Apply dark mode class to page
  if (isDarkMode.value) {
    // Notify all pages to apply dark mode
    uni.setStorageSync('darkMode', 'true')
  } else {
    uni.setStorageSync('darkMode', 'false')
  }

  uni.showToast({
    title: isDarkMode.value ? '已切换深色模式' : '已切换浅色模式',
    icon: 'none',
  })
}
</script>

<style lang="scss" scoped>
.settings-page {
  min-height: 100vh;
  background: var(--bg-secondary, #f5f6fa);
}

.section {
  margin-top: 16rpx;
  background: var(--bg-card, #fff);
  padding: 0 32rpx;
}

.menu-list {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 32rpx 0;
  border-bottom: 1rpx solid var(--border-color, #f5f5f5);

  &:last-child {
    border-bottom: none;
  }
}

.menu-text {
  flex: 1;
  font-size: 28rpx;
  color: var(--text-primary, #333);
}

.menu-arrow {
  font-size: 32rpx;
  color: var(--text-tertiary, #ccc);
}
</style>
