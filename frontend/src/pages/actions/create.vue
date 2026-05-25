<template>
  <view class="create-action-page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">创建行动</text>
      <view class="nav-placeholder" />
    </view>

    <scroll-view class="form-container" scroll-y>
      <!-- 行动标题 -->
      <view class="form-group">
        <text class="form-label">行动标题 *</text>
        <input
          v-model="form.title"
          class="form-input"
          placeholder="请输入行动标题"
          maxlength="256"
        />
      </view>

      <!-- 行动类型 -->
      <view class="form-group">
        <text class="form-label">行动类型 *</text>
        <view class="type-selector">
          <view
            class="type-option"
            :class="{ active: form.action_type === 'todo' }"
            @click="form.action_type = 'todo'"
          >
            <text class="type-icon">✅</text>
            <text class="type-text">待办</text>
            <text class="type-desc">无固定时间</text>
          </view>
          <view
            class="type-option"
            :class="{ active: form.action_type === 'schedule' }"
            @click="form.action_type = 'schedule'"
          >
            <text class="type-icon">📅</text>
            <text class="type-text">日程</text>
            <text class="type-desc">指定日期时间</text>
          </view>
        </view>
      </view>

      <!-- 日期时间设置（仅日程类型显示） -->
      <template v-if="form.action_type === 'schedule'">
        <view class="form-group">
          <text class="form-label">日期</text>
          <picker mode="date" :value="form.scheduled_date" @change="onDateChange">
            <view class="picker-input">
              <text :class="{ placeholder: !form.scheduled_date }">
                {{ form.scheduled_date || '请选择日期' }}
              </text>
              <text class="picker-arrow">›</text>
            </view>
          </picker>
        </view>

        <view class="form-group">
          <text class="form-label">时间</text>
          <picker mode="time" :value="form.scheduled_time" @change="onTimeChange">
            <view class="picker-input">
              <text :class="{ placeholder: !form.scheduled_time }">
                {{ form.scheduled_time || '请选择时间（可选）' }}
              </text>
              <text class="picker-arrow">›</text>
            </view>
          </picker>
        </view>
      </template>

      <!-- 奖励积分 -->
      <view class="form-group">
        <text class="form-label">奖励积分</text>
        <input
          v-model="rewardStr"
          class="form-input"
          type="number"
          placeholder="完成后获得的积分（可选）"
        />
      </view>

      <!-- 关联任务（可选） -->
      <view class="form-group">
        <text class="form-label">关联任务（可选）</text>
        <input
          v-model="form.task_id"
          class="form-input"
          placeholder="输入关联任务ID"
        />
      </view>
    </scroll-view>

    <!-- 提交按钮 -->
    <view class="submit-bar">
      <button
        class="submit-btn"
        :disabled="!canSubmit || actionStore.creating"
        @click="handleSubmit"
      >
        {{ actionStore.creating ? '创建中...' : '创建行动' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useActionStore } from '@/stores/action'
import type { ActionType } from '@/services/types'

const actionStore = useActionStore()

const form = ref({
  title: '',
  action_type: 'todo' as ActionType,
  scheduled_date: '',
  scheduled_time: '',
  task_id: '',
})

const rewardStr = ref('')

const canSubmit = computed(() => form.value.title.trim().length > 0)

function goBack() {
  uni.navigateBack()
}

function onDateChange(e: { detail: { value: string } }) {
  form.value.scheduled_date = e.detail.value
}

function onTimeChange(e: { detail: { value: string } }) {
  form.value.scheduled_time = e.detail.value
}

async function handleSubmit() {
  if (!canSubmit.value) return

  try {
    await actionStore.createAction({
      title: form.value.title.trim(),
      action_type: form.value.action_type,
      scheduled_date: form.value.scheduled_date || undefined,
      scheduled_time: form.value.scheduled_time || undefined,
      task_id: form.value.task_id.trim() || undefined,
      reward_points: rewardStr.value ? parseInt(rewardStr.value) : 0,
    })

    uni.showToast({ title: '创建成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 1000)
  } catch {
    uni.showToast({ title: '创建失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.create-action-page {
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

.form-container {
  flex: 1;
  padding: 24rpx 32rpx;
}

.form-group {
  margin-bottom: 32rpx;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 12rpx;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.type-selector {
  display: flex;
  gap: 24rpx;
}

.type-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32rpx 0;
  background: #fff;
  border-radius: 12rpx;
  border: 2rpx solid #e8e8e8;
  transition: all 0.2s;

  &.active {
    border-color: #4a90d9;
    background: #f0f7ff;
  }
}

.type-icon {
  font-size: 48rpx;
  margin-bottom: 8rpx;
}

.type-text {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.type-desc {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
}

.picker-input {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 80rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.placeholder {
  color: #c0c0c0;
}

.picker-arrow {
  font-size: 32rpx;
  color: #ccc;
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
