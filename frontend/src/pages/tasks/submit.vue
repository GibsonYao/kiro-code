<template>
  <view class="submit-task-page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">提交完成</text>
      <view class="nav-placeholder" />
    </view>

    <scroll-view class="content" scroll-y>
      <!-- 任务信息卡片 -->
      <view v-if="task" class="task-info-card">
        <image
          v-if="task.cover_image_url"
          :src="task.cover_image_url"
          class="task-cover"
          mode="aspectFill"
        />
        <view class="task-detail">
          <text class="task-title">{{ task.title }}</text>
          <text class="task-desc">{{ task.description || '' }}</text>
          <view class="task-meta">
            <text v-if="task.reward_points" class="reward">完成奖励 +{{ task.reward_points }}分</text>
            <text v-if="task.deadline_at" class="deadline">截止：{{ formatDate(task.deadline_at) }}</text>
          </view>
        </view>
      </view>

      <!-- 完成验证 -->
      <view class="verify-section">
        <text class="section-title">完成验证（至少选择一种）</text>

        <!-- 文字描述 -->
        <view class="verify-item">
          <view class="verify-header" @click="toggleVerify('text')">
            <text class="verify-icon">📝</text>
            <text class="verify-label">文字描述</text>
            <text class="verify-toggle">{{ showText ? '收起' : '展开' }}</text>
          </view>
          <view v-if="showText" class="verify-content">
            <textarea
              v-model="evidence.text"
              class="evidence-textarea"
              placeholder="描述你是如何完成这个任务的..."
              :maxlength="500"
            />
          </view>
        </view>

        <!-- 照片上传 -->
        <view class="verify-item">
          <view class="verify-header" @click="toggleVerify('photo')">
            <text class="verify-icon">📷</text>
            <text class="verify-label">照片上传</text>
            <text class="verify-toggle">{{ showPhoto ? '收起' : '展开' }}</text>
          </view>
          <view v-if="showPhoto" class="verify-content">
            <view class="photo-grid">
              <view
                v-for="(photo, index) in evidence.photos"
                :key="index"
                class="photo-item"
              >
                <image :src="photo" class="photo-img" mode="aspectFill" />
                <view class="photo-remove" @click="removePhoto(index)">×</view>
              </view>
              <view
                v-if="evidence.photos.length < 9"
                class="photo-add"
                @click="choosePhoto"
              >
                <text class="add-icon">+</text>
                <text class="add-text">添加照片</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 扫码验证 -->
        <view class="verify-item">
          <view class="verify-header" @click="toggleVerify('qrcode')">
            <text class="verify-icon">📱</text>
            <text class="verify-label">扫码验证</text>
            <text class="verify-toggle">{{ showQrcode ? '收起' : '展开' }}</text>
          </view>
          <view v-if="showQrcode" class="verify-content">
            <view class="qrcode-area">
              <text v-if="evidence.qrcode" class="qrcode-result">已扫描：{{ evidence.qrcode }}</text>
              <button class="scan-btn" @click="scanQrcode">
                {{ evidence.qrcode ? '重新扫码' : '点击扫码' }}
              </button>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 提交按钮 -->
    <view class="submit-bar">
      <button
        class="submit-btn"
        :disabled="!canSubmit || submitting"
        @click="handleSubmit"
      >
        {{ submitting ? '提交中...' : '提交完成' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '@/stores/task'
import { taskApi } from '@/services/api/tasks'
import type { TaskItem } from '@/services/types'

const taskStore = useTaskStore()
const task = ref<TaskItem | null>(null)
const submitting = ref(false)

const showText = ref(true)
const showPhoto = ref(false)
const showQrcode = ref(false)

const evidence = ref({
  text: '',
  photos: [] as string[],
  qrcode: '',
})

const canSubmit = computed(() => {
  return (
    evidence.value.text.trim().length > 0 ||
    evidence.value.photos.length > 0 ||
    evidence.value.qrcode.length > 0
  )
})

onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as { options?: { id?: string } }
  const taskId = currentPage.options?.id

  if (taskId) {
    try {
      task.value = await taskApi.getTask(taskId)
    } catch {
      uni.showToast({ title: '加载任务失败', icon: 'none' })
    }
  }
})

function goBack() {
  uni.navigateBack()
}

function toggleVerify(type: 'text' | 'photo' | 'qrcode') {
  if (type === 'text') showText.value = !showText.value
  else if (type === 'photo') showPhoto.value = !showPhoto.value
  else showQrcode.value = !showQrcode.value
}

function choosePhoto() {
  uni.chooseImage({
    count: 9 - evidence.value.photos.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      evidence.value.photos.push(...res.tempFilePaths)
    },
  })
}

function removePhoto(index: number) {
  evidence.value.photos.splice(index, 1)
}

function scanQrcode() {
  uni.scanCode({
    onlyFromCamera: false,
    success: (res) => {
      evidence.value.qrcode = res.result
    },
    fail: () => {
      uni.showToast({ title: '扫码失败', icon: 'none' })
    },
  })
}

async function handleSubmit() {
  if (!canSubmit.value || !task.value) return

  submitting.value = true
  try {
    await taskStore.submitTask(task.value.id, {
      evidence_text: evidence.value.text.trim() || undefined,
      evidence_photos: evidence.value.photos.length > 0 ? evidence.value.photos : undefined,
      evidence_qrcode: evidence.value.qrcode || undefined,
    })

    uni.showToast({ title: '提交成功，等待审核', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 1500)
  } catch {
    uni.showToast({ title: '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.submit-task-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f6fa;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 88rpx 32rpx 24rpx;
  background: #fff;
}

.nav-back {
  width: 64rpx;
}

.back-icon {
  font-size: 36rpx;
  color: #333;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.nav-placeholder {
  width: 64rpx;
}

.content {
  flex: 1;
  padding: 24rpx 32rpx;
}

.task-info-card {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 32rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.task-cover {
  width: 100%;
  height: 200rpx;
}

.task-detail {
  padding: 24rpx;
}

.task-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.task-desc {
  display: block;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 16rpx;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reward {
  font-size: 26rpx;
  color: #52c41a;
  font-weight: 500;
}

.deadline {
  font-size: 24rpx;
  color: #fa8c16;
}

.verify-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 24rpx;
}

.verify-item {
  margin-bottom: 24rpx;
  border: 1rpx solid #f0f0f0;
  border-radius: 12rpx;
  overflow: hidden;
}

.verify-header {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #fafafa;
}

.verify-icon {
  font-size: 32rpx;
  margin-right: 12rpx;
}

.verify-label {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.verify-toggle {
  font-size: 24rpx;
  color: #4a90d9;
}

.verify-content {
  padding: 24rpx;
}

.evidence-textarea {
  width: 100%;
  height: 200rpx;
  border: 1rpx solid #e8e8e8;
  border-radius: 8rpx;
  padding: 16rpx;
  font-size: 28rpx;
}

.photo-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.photo-item {
  width: 180rpx;
  height: 180rpx;
  position: relative;
  border-radius: 8rpx;
  overflow: hidden;
}

.photo-img {
  width: 100%;
  height: 100%;
}

.photo-remove {
  position: absolute;
  top: 4rpx;
  right: 4rpx;
  width: 40rpx;
  height: 40rpx;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
}

.photo-add {
  width: 180rpx;
  height: 180rpx;
  border: 2rpx dashed #d9d9d9;
  border-radius: 8rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.add-icon {
  font-size: 48rpx;
  color: #999;
}

.add-text {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
}

.qrcode-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.qrcode-result {
  font-size: 26rpx;
  color: #52c41a;
  word-break: break-all;
}

.scan-btn {
  background: #4a90d9;
  color: #fff;
  font-size: 28rpx;
  border-radius: 8rpx;
  padding: 16rpx 48rpx;
}

.submit-bar {
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &[disabled] {
    opacity: 0.5;
  }
}
</style>
