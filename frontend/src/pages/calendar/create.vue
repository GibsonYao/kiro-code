<template>
  <view class="create-event-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">{{ isEdit ? '编辑事件' : '新建事件' }}</text>
      <view class="nav-right">
        <text v-if="isEdit" class="delete-btn" @click="handleDelete">删除</text>
      </view>
    </view>

    <scroll-view class="form-container" scroll-y>
      <!-- 标题 -->
      <view class="form-group">
        <text class="form-label">事件标题 *</text>
        <input
          v-model="form.title"
          class="form-input"
          placeholder="请输入事件标题"
          maxlength="256"
        />
      </view>

      <!-- 事件类型 -->
      <view class="form-group">
        <text class="form-label">事件类型 *</text>
        <view class="type-selector">
          <view
            class="type-option"
            :class="{ active: form.event_type === 'schedule' }"
            @click="form.event_type = 'schedule'"
          >
            <text class="type-icon">📅</text>
            <text class="type-text">日程</text>
          </view>
          <view
            class="type-option"
            :class="{ active: form.event_type === 'todo' }"
            @click="form.event_type = 'todo'"
          >
            <text class="type-icon">✅</text>
            <text class="type-text">待办</text>
          </view>
          <view
            class="type-option"
            :class="{ active: form.event_type === 'anniversary' }"
            @click="form.event_type = 'anniversary'"
          >
            <text class="type-icon">🎂</text>
            <text class="type-text">纪念日</text>
          </view>
        </view>
      </view>

      <!-- 日期 -->
      <view class="form-group">
        <text class="form-label">日期</text>
        <picker mode="date" :value="form.event_date" @change="onDateChange">
          <view class="picker-input">
            <text :class="{ placeholder: !form.event_date }">
              {{ form.event_date || '请选择日期' }}
            </text>
            <text class="picker-arrow">›</text>
          </view>
        </picker>
      </view>

      <!-- 时间（非纪念日） -->
      <view class="form-group" v-if="form.event_type !== 'anniversary'">
        <text class="form-label">时间（可选）</text>
        <picker mode="time" :value="form.event_time" @change="onTimeChange">
          <view class="picker-input">
            <text :class="{ placeholder: !form.event_time }">
              {{ form.event_time || '请选择时间' }}
            </text>
            <text class="picker-arrow">›</text>
          </view>
        </picker>
      </view>

      <!-- 是否重复 -->
      <view class="form-group">
        <view class="switch-row">
          <text class="form-label inline">每年重复</text>
          <switch :checked="form.is_recurring" @change="onRecurringChange" color="#4a90d9" />
        </view>
      </view>

      <!-- 提前提醒 -->
      <view class="form-group">
        <text class="form-label">提前提醒（天）</text>
        <input
          v-model="remindDaysStr"
          class="form-input"
          type="number"
          placeholder="提前几天提醒（0表示不提醒）"
        />
      </view>
    </scroll-view>

    <!-- 提交按钮 -->
    <view class="submit-bar">
      <button
        class="submit-btn"
        :disabled="!canSubmit || submitting"
        @click="handleSubmit"
      >
        {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '创建事件') }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { calendarApi } from '@/services/api/calendar'
import type { CalendarEventType } from '@/services/types'

const isEdit = ref(false)
const editId = ref('')
const submitting = ref(false)

const form = ref({
  title: '',
  event_type: 'schedule' as CalendarEventType,
  event_date: '',
  event_time: '',
  is_recurring: false,
})

const remindDaysStr = ref('0')

const canSubmit = computed(() => form.value.title.trim().length > 0)

onLoad((query) => {
  if (query?.id) {
    isEdit.value = true
    editId.value = query.id
    loadEvent(query.id)
  } else {
    if (query?.date) {
      form.value.event_date = query.date
    }
    if (query?.type && ['schedule', 'todo', 'anniversary'].includes(query.type)) {
      form.value.event_type = query.type as CalendarEventType
    }
  }
})

async function loadEvent(id: string) {
  try {
    const event = await calendarApi.getEvent(id)
    form.value.title = event.title
    form.value.event_type = event.event_type
    form.value.event_date = event.event_date || ''
    form.value.event_time = event.event_time || ''
    form.value.is_recurring = event.is_recurring
    remindDaysStr.value = String(event.remind_before_days || 0)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function goBack() {
  uni.navigateBack()
}

function onDateChange(e: { detail: { value: string } }) {
  form.value.event_date = e.detail.value
}

function onTimeChange(e: { detail: { value: string } }) {
  form.value.event_time = e.detail.value
}

function onRecurringChange(e: { detail: { value: boolean } }) {
  form.value.is_recurring = e.detail.value
}

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    const data = {
      title: form.value.title.trim(),
      event_type: form.value.event_type,
      event_date: form.value.event_date || undefined,
      event_time: form.value.event_time || undefined,
      is_recurring: form.value.is_recurring,
      remind_before_days: parseInt(remindDaysStr.value) || 0,
    }

    if (isEdit.value) {
      await calendarApi.updateEvent(editId.value, data)
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      await calendarApi.createEvent(data)
      uni.showToast({ title: '创建成功', icon: 'success' })
    }
    setTimeout(() => uni.navigateBack(), 1000)
  } catch {
    uni.showToast({ title: isEdit.value ? '保存失败' : '创建失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  uni.showModal({
    title: '确认删除',
    content: '删除后不可恢复，确定要删除这个事件吗？',
    confirmColor: '#f5222d',
    success: async (res) => {
      if (res.confirm) {
        try {
          await calendarApi.deleteEvent(editId.value)
          uni.showToast({ title: '已删除', icon: 'success' })
          setTimeout(() => uni.navigateBack(), 800)
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
}
</script>

<style lang="scss" scoped>
.create-event-page {
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

.nav-right {
  width: 64rpx;
  display: flex;
  justify-content: flex-end;
}

.delete-btn {
  font-size: 28rpx;
  color: #f5222d;
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

  &.inline {
    display: inline;
    margin-bottom: 0;
  }
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
  gap: 16rpx;
}

.type-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 0;
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
  font-size: 40rpx;
  margin-bottom: 8rpx;
}

.type-text {
  font-size: 24rpx;
  color: #333;
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

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 20rpx 24rpx;
  border-radius: 12rpx;
  border: 1rpx solid #e8e8e8;
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
