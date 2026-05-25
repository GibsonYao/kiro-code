<template>
  <view class="calendar-page">
    <view class="page-header">
      <text class="page-title">我的日历</text>
    </view>
    <view class="page-content">
      <view class="card">
        <text class="card-text">日历功能即将上线</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { checkAuth } from '@/utils/route-guard'

onShow(() => {
  checkAuth()
})
</script>

<style lang="scss" scoped>
.calendar-page {
  padding: $spacing-lg;
}

.page-header {
  padding: $spacing-lg 0;

  .page-title {
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
    color: $color-text-primary;
  }
}

.page-content {
  .card-text {
    font-size: $font-size-md;
    color: $color-text-secondary;
  }
}
</style>
