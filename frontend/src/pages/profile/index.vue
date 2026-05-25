<template>
  <view class="profile-page">
    <view class="profile-header">
      <image class="avatar" :src="userStore.avatarUrl || '/static/default-avatar.png'" mode="aspectFill" />
      <text class="nickname">{{ userStore.nickname || '未设置昵称' }}</text>
      <text class="family-name" v-if="userStore.currentFamily">
        {{ userStore.currentFamily.name }}
      </text>
    </view>

    <view class="profile-menu">
      <view class="menu-item card" @tap="handleLogout">
        <text class="menu-text danger">退出登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { checkAuth } from '@/utils/route-guard'

const userStore = useUserStore()

onShow(() => {
  checkAuth()
})

function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
      }
    },
  })
}
</script>

<style lang="scss" scoped>
.profile-page {
  padding: $spacing-lg;
}

.profile-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $spacing-xxl 0;

  .avatar {
    width: 160rpx;
    height: 160rpx;
    border-radius: 50%;
    margin-bottom: $spacing-md;
    background-color: $color-border;
  }

  .nickname {
    font-size: $font-size-xl;
    font-weight: $font-weight-semibold;
    color: $color-text-primary;
    margin-bottom: $spacing-xs;
  }

  .family-name {
    font-size: $font-size-md;
    color: $color-text-secondary;
  }
}

.profile-menu {
  .menu-item {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $spacing-lg;
  }

  .menu-text {
    font-size: $font-size-base;
    color: $color-text-primary;

    &.danger {
      color: $color-danger;
    }
  }
}
</style>
