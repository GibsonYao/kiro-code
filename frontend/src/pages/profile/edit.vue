<template>
  <view class="edit-profile-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">编辑资料</text>
      <view class="nav-right" />
    </view>

    <!-- 头像区域 -->
    <view class="avatar-section" @click="chooseAvatar">
      <image
        class="avatar-preview"
        :src="avatarUrl || '/static/default-avatar.png'"
        mode="aspectFill"
      />
      <text class="avatar-hint">点击更换头像</text>
    </view>

    <!-- 表单 -->
    <view class="form-section">
      <view class="form-item">
        <text class="form-label">昵称</text>
        <input
          v-model="nickname"
          class="form-input"
          placeholder="请输入昵称"
          maxlength="20"
        />
      </view>
    </view>

    <!-- 保存按钮 -->
    <view class="btn-section">
      <button class="save-btn" :disabled="saving" @click="handleSave">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { put } from '@/services/request'

const userStore = useUserStore()

const nickname = ref('')
const avatarUrl = ref('')
const avatarFile = ref('')
const saving = ref(false)

onLoad(() => {
  nickname.value = userStore.nickname || ''
  avatarUrl.value = userStore.avatarUrl || ''
})

function chooseAvatar() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempPath = res.tempFilePaths[0]
      avatarUrl.value = tempPath
      avatarFile.value = tempPath
    },
  })
}

async function handleSave() {
  if (!nickname.value.trim()) {
    uni.showToast({ title: '请输入昵称', icon: 'none' })
    return
  }

  saving.value = true
  try {
    const data: Record<string, unknown> = { nickname: nickname.value.trim() }

    // If avatar was changed, upload it first
    if (avatarFile.value) {
      try {
        const uploadRes = await new Promise<string>((resolve, reject) => {
          uni.uploadFile({
            url: '/api/v1/auth/me/avatar',
            filePath: avatarFile.value,
            name: 'file',
            header: {
              Authorization: `Bearer ${uni.getStorageSync('token')}`,
            },
            success: (res) => {
              if (res.statusCode === 200) {
                const result = JSON.parse(res.data)
                resolve(result.avatar_url || '')
              } else {
                reject(new Error('Upload failed'))
              }
            },
            fail: reject,
          })
        })
        if (uploadRes) {
          data.avatar_url = uploadRes
        }
      } catch {
        // Avatar upload failed, continue with nickname update
      }
    }

    await put('/auth/me', data)
    await userStore.fetchUserInfo()
    uni.showToast({ title: '保存成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.edit-profile-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 88rpx 32rpx 24rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.nav-back {
  width: 64rpx;
}

.back-icon {
  font-size: 36rpx;
  color: #fff;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #fff;
}

.nav-right {
  width: 64rpx;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48rpx 0;
  background: #fff;
  margin-bottom: 16rpx;
}

.avatar-preview {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  border: 4rpx solid #e8e8e8;
  margin-bottom: 16rpx;
  background: #f5f6fa;
}

.avatar-hint {
  font-size: 24rpx;
  color: #4a90d9;
}

.form-section {
  background: #fff;
  padding: 0 32rpx;
  margin-bottom: 16rpx;
}

.form-item {
  display: flex;
  align-items: center;
  padding: 32rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.form-label {
  font-size: 28rpx;
  color: #333;
  width: 140rpx;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
  font-size: 28rpx;
  color: #333;
  text-align: right;
}

.btn-section {
  padding: 48rpx 32rpx;
}

.save-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 30rpx;
  font-weight: 600;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &[disabled] {
    opacity: 0.6;
  }
}
</style>
