<template>
  <view class="invite-page">
    <!-- 邀请码展示区 -->
    <view class="invite-section" v-if="familyStore.currentFamily">
      <text class="section-title">分享邀请码</text>
      <view class="invite-card">
        <text class="invite-label">{{ familyStore.currentFamily.name }} 的邀请码</text>
        <text class="invite-code">{{ familyStore.inviteCode }}</text>
        <button class="copy-btn" @click="copyInviteCode">复制邀请码</button>
        <text class="invite-hint">将邀请码分享给家人，对方输入即可加入</text>
      </view>
    </view>

    <!-- 输入邀请码加入 -->
    <view class="join-section">
      <text class="section-title">加入其他家庭</text>
      <view class="join-card">
        <input
          v-model="joinCode"
          class="join-input"
          placeholder="请输入邀请码"
          maxlength="20"
        />
        <button class="join-btn" :disabled="!joinCode.trim()" @click="handleJoin">
          加入家庭
        </button>
      </view>
    </view>

    <!-- 创建新家庭 -->
    <view class="create-section">
      <text class="section-title">创建新家庭</text>
      <view class="create-card">
        <input
          v-model="newFamilyName"
          class="create-input"
          placeholder="请输入家庭名称"
          maxlength="50"
        />
        <button class="create-btn" :disabled="!newFamilyName.trim()" @click="handleCreate">
          创建家庭
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useFamilyStore } from '@/stores/family'

const familyStore = useFamilyStore()

const joinCode = ref('')
const newFamilyName = ref('')

onShow(() => {
  familyStore.fetchCurrentFamily()
})

function copyInviteCode() {
  uni.setClipboardData({
    data: familyStore.inviteCode,
    success: () => uni.showToast({ title: '已复制', icon: 'success' }),
  })
}

async function handleJoin() {
  if (!joinCode.value.trim()) return
  try {
    await familyStore.joinFamily(joinCode.value.trim())
    uni.showToast({ title: '加入成功', icon: 'success' })
    joinCode.value = ''
    setTimeout(() => uni.navigateBack(), 1000)
  } catch {
    uni.showToast({ title: '加入失败，请检查邀请码', icon: 'none' })
  }
}

async function handleCreate() {
  if (!newFamilyName.value.trim()) return
  try {
    await familyStore.createFamily(newFamilyName.value.trim())
    uni.showToast({ title: '创建成功', icon: 'success' })
    newFamilyName.value = ''
    setTimeout(() => uni.navigateBack(), 1000)
  } catch {
    uni.showToast({ title: '创建失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.invite-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding: 24rpx;
  padding-bottom: env(safe-area-inset-bottom);
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
}

.invite-section, .join-section, .create-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.invite-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12rpx;
  padding: 32rpx;
  text-align: center;
}

.invite-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  display: block;
  margin-bottom: 16rpx;
}

.invite-code {
  font-size: 48rpx;
  font-weight: 700;
  color: #fff;
  letter-spacing: 8rpx;
  display: block;
  margin-bottom: 24rpx;
}

.copy-btn {
  width: 280rpx;
  height: 72rpx;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 28rpx;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16rpx;
}

.invite-hint {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.7);
}

.join-card, .create-card {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.join-input, .create-input {
  width: 100%;
  height: 80rpx;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.join-btn, .create-btn {
  height: 80rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &[disabled] {
    opacity: 0.5;
  }
}

.create-btn {
  background: #52c41a;
}
</style>
