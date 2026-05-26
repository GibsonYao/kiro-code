<template>
  <view class="anniversary-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">纪念日管理</text>
      <view class="nav-right">
        <text class="add-link" @click="showAddForm = true">+ 添加</text>
      </view>
    </view>

    <scroll-view class="content" scroll-y>
      <!-- 添加/编辑表单 -->
      <view v-if="showAddForm" class="add-form-card">
        <text class="form-card-title">{{ editingId ? '编辑纪念日' : '添加纪念日' }}</text>
        <view class="form-group">
          <text class="form-label">纪念日名称 *</text>
          <input
            v-model="formTitle"
            class="form-input"
            placeholder="如：结婚纪念日、妈妈生日"
            maxlength="100"
          />
        </view>
        <view class="form-group">
          <text class="form-label">日期 *</text>
          <picker mode="date" :value="formDate" @change="onFormDateChange">
            <view class="picker-input">
              <text :class="{ placeholder: !formDate }">
                {{ formDate || '请选择日期' }}
              </text>
              <text class="picker-arrow">›</text>
            </view>
          </picker>
        </view>
        <view class="form-group">
          <text class="form-label">提前提醒（天）</text>
          <input
            v-model="formRemindDays"
            class="form-input"
            type="number"
            placeholder="提前几天提醒（默认3天）"
          />
        </view>
        <view class="form-actions">
          <view class="cancel-btn" @click="cancelForm">
            <text>取消</text>
          </view>
          <view class="save-btn" :class="{ disabled: !canSave }" @click="handleSave">
            <text>{{ saving ? '保存中...' : '保存' }}</text>
          </view>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="loading" class="loading-state">
        <text>加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="anniversaries.length === 0 && !showAddForm" class="empty-state">
        <text class="empty-emoji">🎂</text>
        <text class="empty-text">还没有纪念日</text>
        <text class="empty-hint">添加家人生日、结婚纪念日等重要日子</text>
        <view class="empty-btn" @click="showAddForm = true">
          <text>添加纪念日</text>
        </view>
      </view>

      <!-- 纪念日列表 -->
      <view v-else class="anniversary-list">
        <view
          v-for="item in anniversaries"
          :key="item.id"
          class="anniversary-card"
        >
          <view class="card-header">
            <view class="card-icon">🎂</view>
            <view class="card-info">
              <text class="card-title">{{ item.title }}</text>
              <text class="card-date">{{ item.event_date }}</text>
            </view>
            <view class="card-actions">
              <text class="edit-btn" @click="startEdit(item)">编辑</text>
              <text class="del-btn" @click="handleDelete(item.id)">删除</text>
            </view>
          </view>

          <!-- AI祝福文案 -->
          <view class="blessing-section">
            <view class="blessing-header">
              <text class="blessing-label">✨ AI祝福文案</text>
              <text class="refresh-btn" @click="generateBlessing(item)">刷新</text>
            </view>
            <view class="blessing-content">
              <text class="blessing-text">
                {{ blessings[item.id] || getDefaultBlessing(item.title) }}
              </text>
            </view>
          </view>

          <!-- 倒计时 -->
          <view class="countdown-row">
            <text class="countdown-label">距离下次</text>
            <text class="countdown-value">{{ getDaysUntil(item.event_date) }}天</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { calendarApi } from '@/services/api/calendar'
import type { CalendarEventItem } from '@/services/types'

const anniversaries = ref<CalendarEventItem[]>([])
const loading = ref(false)
const showAddForm = ref(false)
const saving = ref(false)
const editingId = ref('')

const formTitle = ref('')
const formDate = ref('')
const formRemindDays = ref('3')

const blessings = ref<Record<string, string>>({})

const canSave = computed(() => formTitle.value.trim().length > 0 && formDate.value.length > 0)

async function fetchAnniversaries() {
  loading.value = true
  try {
    const res = await calendarApi.getAnniversaries({ page_size: 100 })
    anniversaries.value = res.items
  } catch {
    anniversaries.value = []
  } finally {
    loading.value = false
  }
}

function onFormDateChange(e: { detail: { value: string } }) {
  formDate.value = e.detail.value
}

function cancelForm() {
  showAddForm.value = false
  editingId.value = ''
  formTitle.value = ''
  formDate.value = ''
  formRemindDays.value = '3'
}

function startEdit(item: CalendarEventItem) {
  editingId.value = item.id
  formTitle.value = item.title
  formDate.value = item.event_date || ''
  formRemindDays.value = String(item.remind_before_days || 3)
  showAddForm.value = true
}

async function handleSave() {
  if (!canSave.value || saving.value) return

  saving.value = true
  try {
    if (editingId.value) {
      await calendarApi.updateEvent(editingId.value, {
        title: formTitle.value.trim(),
        event_date: formDate.value,
        remind_before_days: parseInt(formRemindDays.value) || 3,
      })
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      await calendarApi.createAnniversary({
        title: formTitle.value.trim(),
        event_date: formDate.value,
        remind_before_days: parseInt(formRemindDays.value) || 3,
      })
      uni.showToast({ title: '添加成功', icon: 'success' })
    }
    cancelForm()
    fetchAnniversaries()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: string) {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个纪念日吗？',
    confirmColor: '#f5222d',
    success: async (res) => {
      if (res.confirm) {
        try {
          await calendarApi.deleteEvent(id)
          uni.showToast({ title: '已删除', icon: 'success' })
          fetchAnniversaries()
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
}

function getDaysUntil(dateStr: string | null): number {
  if (!dateStr) return 0
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const parts = dateStr.split('-')
  const targetMonth = parseInt(parts[1])
  const targetDay = parseInt(parts[2])

  let nextDate = new Date(today.getFullYear(), targetMonth - 1, targetDay)
  if (nextDate < today) {
    nextDate = new Date(today.getFullYear() + 1, targetMonth - 1, targetDay)
  }
  const diff = Math.ceil((nextDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diff
}

function getDefaultBlessing(title: string): string {
  const templates = [
    `祝${title}快乐！愿每一天都充满幸福和温暖 🎉`,
    `${title}到了，愿所有美好如期而至 ✨`,
    `在这个特别的日子里，送上最真挚的祝福 💝`,
  ]
  return templates[Math.floor(Math.random() * templates.length)]
}

function generateBlessing(item: CalendarEventItem) {
  // Simulate AI generating blessing text
  const templates = [
    `亲爱的，${item.title}快乐！愿你的每一天都如阳光般灿烂 ☀️`,
    `今天是${item.title}，感恩有你，愿未来的日子更加美好 💕`,
    `${item.title}到了！让我们一起庆祝这个特别的日子 🎊`,
    `在${item.title}这天，愿所有的幸福都围绕着你 🌟`,
  ]
  blessings.value[item.id] = templates[Math.floor(Math.random() * templates.length)]
}

function goBack() {
  uni.navigateBack()
}

onMounted(() => {
  fetchAnniversaries()
})
</script>

<style lang="scss" scoped>
.anniversary-page {
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
  background: linear-gradient(135deg, #fa8c16 0%, #f5222d 100%);
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
  width: 80rpx;
  display: flex;
  justify-content: flex-end;
}

.add-link {
  font-size: 28rpx;
  color: #fff;
}

.content {
  flex: 1;
  padding: 24rpx 32rpx;
}

.add-form-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.form-card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 24rpx;
}

.form-group {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 8rpx;
}

.form-input {
  width: 100%;
  height: 72rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.picker-input {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 72rpx;
  background: #f9f9fb;
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

.form-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 16rpx;
}

.cancel-btn {
  flex: 1;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f5;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #666;
}

.save-btn {
  flex: 1;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fa8c16;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #fff;

  &.disabled {
    opacity: 0.5;
  }
}

.loading-state {
  text-align: center;
  padding: 80rpx;
  color: #999;
  font-size: 26rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 160rpx;
}

.empty-emoji {
  font-size: 96rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #333;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: #999;
  margin-bottom: 48rpx;
}

.empty-btn {
  padding: 20rpx 48rpx;
  background: #fa8c16;
  border-radius: 40rpx;
  color: #fff;
  font-size: 28rpx;
}

.anniversary-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.anniversary-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.card-icon {
  font-size: 48rpx;
  margin-right: 16rpx;
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
}

.card-date {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-top: 4rpx;
}

.card-actions {
  display: flex;
  gap: 16rpx;
}

.edit-btn {
  font-size: 24rpx;
  color: #4a90d9;
}

.del-btn {
  font-size: 24rpx;
  color: #f5222d;
}

.blessing-section {
  background: #fffbe6;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 16rpx;
}

.blessing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.blessing-label {
  font-size: 24rpx;
  color: #fa8c16;
  font-weight: 500;
}

.refresh-btn {
  font-size: 22rpx;
  color: #4a90d9;
}

.blessing-content {
  padding: 0;
}

.blessing-text {
  font-size: 26rpx;
  color: #333;
  line-height: 1.6;
}

.countdown-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12rpx;
  border-top: 1rpx solid #f0f0f0;
}

.countdown-label {
  font-size: 24rpx;
  color: #999;
}

.countdown-value {
  font-size: 28rpx;
  font-weight: 600;
  color: #f5222d;
}
</style>
