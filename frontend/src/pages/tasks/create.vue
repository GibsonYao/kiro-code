<template>
  <view class="create-task-page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">{{ isEdit ? '编辑任务' : '创建任务' }}</text>
      <view class="nav-right">
        <text v-if="isEdit" class="delete-btn" @click="handleDelete">删除</text>
      </view>
    </view>

    <scroll-view class="form-container" scroll-y>
      <!-- 任务标题 -->
      <view class="form-group">
        <text class="form-label">任务标题 *</text>
        <input
          v-model="form.title"
          class="form-input"
          placeholder="请输入任务标题"
          maxlength="256"
        />
      </view>

      <!-- 任务描述 -->
      <view class="form-group">
        <text class="form-label">任务描述</text>
        <textarea
          v-model="form.description"
          class="form-textarea"
          placeholder="请输入任务描述（可选）"
          :maxlength="1000"
        />
      </view>

      <!-- 任务类型 -->
      <view class="form-group">
        <text class="form-label">任务类型 *</text>
        <view class="type-selector">
          <view
            class="type-option"
            :class="{ active: form.task_type === 'once' }"
            @click="form.task_type = 'once'"
          >
            <text class="type-icon">📋</text>
            <text class="type-text">单次任务</text>
          </view>
          <view
            class="type-option"
            :class="{ active: form.task_type === 'recurring' }"
            @click="form.task_type = 'recurring'"
          >
            <text class="type-icon">🔄</text>
            <text class="type-text">重复任务</text>
          </view>
        </view>
      </view>

      <!-- 时限设置 -->
      <view class="form-group">
        <text class="form-label">时限（小时）</text>
        <input
          v-model="timeLimitStr"
          class="form-input"
          type="digit"
          placeholder="认领后需在此时间内完成（可选）"
        />
      </view>

      <!-- 积分奖惩 -->
      <view class="form-group">
        <text class="form-label">积分设置</text>
        <view class="points-row">
          <view class="points-item">
            <text class="points-label">奖励积分</text>
            <input
              v-model="rewardStr"
              class="points-input"
              type="number"
              placeholder="0"
            />
          </view>
          <view class="points-item">
            <text class="points-label">惩罚积分</text>
            <input
              v-model="penaltyStr"
              class="points-input penalty"
              type="number"
              placeholder="0"
            />
          </view>
        </view>
      </view>

      <!-- 关联计划（可选） -->
      <view class="form-group">
        <text class="form-label">关联计划步骤（可选）</text>
        <input
          v-model="form.plan_step_id"
          class="form-input"
          placeholder="输入计划步骤ID（可选）"
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
        {{ submitting ? (isEdit ? '保存中...' : '创建中...') : (isEdit ? '保存修改' : '创建任务') }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTaskStore } from '@/stores/task'
import { taskApi } from '@/services/api/tasks'
import type { TaskType } from '@/services/types'

const taskStore = useTaskStore()

const isEdit = ref(false)
const editId = ref('')
const submitting = ref(false)

const form = ref({
  title: '',
  description: '',
  task_type: 'once' as TaskType,
  plan_step_id: '',
})

const timeLimitStr = ref('')
const rewardStr = ref('')
const penaltyStr = ref('')

const canSubmit = computed(() => form.value.title.trim().length > 0)

onLoad((query) => {
  const id = query?.id
  if (id) {
    isEdit.value = true
    editId.value = id
    loadTask(id)
  }
})

async function loadTask(id: string) {
  try {
    const task = await taskApi.getTask(id)
    form.value.title = task.title
    form.value.description = task.description || ''
    form.value.task_type = task.task_type
    form.value.plan_step_id = task.plan_step_id || ''
    timeLimitStr.value = task.time_limit_hours ? String(task.time_limit_hours) : ''
    rewardStr.value = task.reward_points ? String(task.reward_points) : ''
    penaltyStr.value = task.penalty_points ? String(task.penalty_points) : ''
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function goBack() {
  uni.navigateBack()
}

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    const data = {
      title: form.value.title.trim(),
      description: form.value.description.trim() || undefined,
      task_type: form.value.task_type,
      plan_step_id: form.value.plan_step_id.trim() || undefined,
      time_limit_hours: timeLimitStr.value ? parseFloat(timeLimitStr.value) : undefined,
      reward_points: rewardStr.value ? parseInt(rewardStr.value) : 0,
      penalty_points: penaltyStr.value ? parseInt(penaltyStr.value) : 0,
    }

    if (isEdit.value) {
      await taskApi.updateTask(editId.value, data)
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      await taskStore.createTask(data)
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
    content: '删除后不可恢复，确定要删除这个任务吗？',
    confirmColor: '#f5222d',
    success: async (res) => {
      if (res.confirm) {
        try {
          await taskStore.deleteTask(editId.value)
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
.create-task-page {
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

.form-textarea {
  width: 100%;
  height: 200rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
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
  font-size: 26rpx;
  color: #333;
}

.points-row {
  display: flex;
  gap: 24rpx;
}

.points-item {
  flex: 1;
}

.points-label {
  display: block;
  font-size: 24rpx;
  color: #666;
  margin-bottom: 8rpx;
}

.points-input {
  width: 100%;
  height: 72rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
  color: #52c41a;

  &.penalty {
    color: #f5222d;
  }
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
