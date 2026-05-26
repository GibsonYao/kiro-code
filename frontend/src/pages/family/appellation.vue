<template>
  <view class="appellation-page">
    <view class="page-header">
      <text class="page-title">称谓设置</text>
      <text class="page-desc">设置家庭成员之间的称谓关系</text>
    </view>

    <view v-if="familyStore.loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else class="member-list">
      <view
        v-for="member in familyStore.members"
        :key="member.id"
        class="member-row"
      >
        <view class="member-left">
          <image
            class="member-avatar"
            :src="member.user_avatar_url || '/static/default-avatar.png'"
            mode="aspectFill"
          />
          <text class="member-name">{{ member.user_nickname || '未设置' }}</text>
        </view>
        <view class="member-right">
          <input
            class="appellation-input"
            :value="member.appellation || ''"
            :placeholder="member.relationship || '设置称谓'"
            @blur="(e: any) => handleBlur(member.id, e.detail.value)"
            maxlength="20"
          />
        </view>
      </view>
    </view>

    <view v-if="!familyStore.loading && familyStore.members.length === 0" class="empty">
      <text class="empty-text">暂无家庭成员</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { useFamilyStore } from '@/stores/family'

const familyStore = useFamilyStore()

onShow(() => {
  familyStore.fetchMembers()
})

async function handleBlur(memberId: string, value: string) {
  if (!value.trim()) return
  // 检查是否有变化
  const member = familyStore.members.find(m => m.id === memberId)
  if (member && member.appellation === value.trim()) return

  try {
    await familyStore.setAppellation(memberId, value.trim())
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.appellation-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding: 24rpx;
  padding-bottom: env(safe-area-inset-bottom);
}

.page-header {
  padding: 24rpx 0 32rpx;
}

.page-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.page-desc {
  font-size: 26rpx;
  color: #999;
}

.loading {
  padding: 64rpx 0;
  text-align: center;
  color: #999;
}

.member-list {
  background: #fff;
  border-radius: 16rpx;
  padding: 12rpx 24rpx;
}

.member-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.member-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.member-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #e8e8e8;
}

.member-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.member-right {
  flex-shrink: 0;
  width: 200rpx;
}

.appellation-input {
  width: 100%;
  height: 64rpx;
  background: #f5f6fa;
  border-radius: 8rpx;
  padding: 0 16rpx;
  font-size: 26rpx;
  text-align: center;
  border: 1rpx solid #e8e8e8;
}

.empty {
  padding: 64rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: #999;
}
</style>
