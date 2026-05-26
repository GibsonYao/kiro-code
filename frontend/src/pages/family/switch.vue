<template>
  <view class="switch-page">
    <view class="page-header">
      <text class="page-title">我的家庭</text>
      <text class="page-desc">选择要切换的家庭</text>
    </view>

    <!-- 家庭列表 -->
    <view class="family-list">
      <view
        v-for="family in familyStore.myFamilies"
        :key="family.family_id"
        class="family-item"
        :class="{ active: family.is_current }"
        @click="handleSwitch(family)"
      >
        <view class="family-info">
          <text class="family-name">{{ family.family_name }}</text>
          <view class="family-meta">
            <text class="family-role">{{ family.role === 'admin' ? '管理员' : '成员' }}</text>
            <text v-if="family.is_current" class="current-tag">当前</text>
          </view>
        </view>
        <text v-if="family.is_current" class="check-icon">✓</text>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-if="familyStore.myFamilies.length === 0" class="empty">
      <text class="empty-text">暂未加入任何家庭</text>
    </view>

    <!-- 创建新家庭 -->
    <view class="create-section">
      <button class="create-btn" @click="showCreateModal = true">
        + 创建新家庭
      </button>
    </view>

    <!-- 创建家庭弹窗 -->
    <view v-if="showCreateModal" class="modal-mask" @click="showCreateModal = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">创建家庭</text>
        <input
          v-model="newFamilyName"
          class="modal-input"
          placeholder="请输入家庭名称"
          maxlength="50"
        />
        <view class="modal-actions">
          <button class="modal-cancel" @click="showCreateModal = false">取消</button>
          <button class="modal-confirm" @click="handleCreate">创建</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useFamilyStore } from '@/stores/family'
import type { UserFamilyItem } from '@/stores/family'

const familyStore = useFamilyStore()

const showCreateModal = ref(false)
const newFamilyName = ref('')

onShow(() => {
  familyStore.fetchMyFamilies()
})

async function handleSwitch(family: UserFamilyItem) {
  if (family.is_current) return
  try {
    await familyStore.switchFamily(family.family_id)
    uni.showToast({ title: '已切换', icon: 'success' })
  } catch {
    uni.showToast({ title: '切换失败', icon: 'none' })
  }
}

async function handleCreate() {
  if (!newFamilyName.value.trim()) {
    uni.showToast({ title: '请输入家庭名称', icon: 'none' })
    return
  }
  try {
    await familyStore.createFamily(newFamilyName.value.trim())
    showCreateModal.value = false
    newFamilyName.value = ''
    uni.showToast({ title: '创建成功', icon: 'success' })
  } catch {
    uni.showToast({ title: '创建失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.switch-page {
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

.family-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.family-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-radius: 12rpx;
  padding: 28rpx 24rpx;
  border: 2rpx solid transparent;

  &.active {
    border-color: #4a90d9;
    background: #f0f7ff;
  }
}

.family-info {
  flex: 1;
}

.family-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.family-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.family-role {
  font-size: 22rpx;
  color: #4a90d9;
  background: #e6f7ff;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
}

.current-tag {
  font-size: 22rpx;
  color: #52c41a;
  background: #f6ffed;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
}

.check-icon {
  font-size: 36rpx;
  color: #4a90d9;
  font-weight: 600;
}

.empty {
  padding: 64rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: #999;
}

.create-section {
  margin-top: 32rpx;
}

.create-btn {
  width: 100%;
  height: 88rpx;
  background: #fff;
  color: #4a90d9;
  font-size: 28rpx;
  border-radius: 12rpx;
  border: 2rpx dashed #4a90d9;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 弹窗 */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal-content {
  width: 560rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 48rpx 32rpx;
}

.modal-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  text-align: center;
  display: block;
  margin-bottom: 32rpx;
}

.modal-input {
  width: 100%;
  height: 80rpx;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
  margin-bottom: 32rpx;
}

.modal-actions {
  display: flex;
  gap: 24rpx;
}

.modal-cancel {
  flex: 1;
  height: 80rpx;
  background: #f5f6fa;
  color: #666;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-confirm {
  flex: 1;
  height: 80rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
