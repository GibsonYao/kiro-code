<template>
  <view class="action-page">
    <!-- Tab切换：待办 / 日程 -->
    <view class="tab-bar">
      <view
        class="tab-item"
        :class="{ active: activeTab === 'todo' }"
        @click="switchTab('todo')"
      >
        待办
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'schedule' }"
        @click="switchTab('schedule')"
      >
        日程
      </view>
    </view>

    <!-- 行动列表 -->
    <scroll-view
      class="action-list"
      scroll-y
      @scrolltolower="handleLoadMore"
    >
      <view v-if="actionStore.isEmpty" class="empty-state">
        <text class="empty-text">暂无{{ activeTab === 'todo' ? '待办' : '日程' }}</text>
        <button class="create-btn" @click="goCreate">创建行动</button>
      </view>

      <view
        v-for="action in filteredActions"
        :key="action.id"
        class="action-card"
      >
        <image
          v-if="action.cover_image_url"
          :src="action.cover_image_url"
          class="action-cover"
          mode="aspectFill"
        />
        <view class="action-info">
          <view class="action-header">
            <text class="action-title">{{ action.title }}</text>
            <view class="action-status" :class="'status-' + action.status">
              {{ statusLabel(action.status) }}
            </view>
          </view>

          <text v-if="action.display_text" class="action-desc">{{ action.display_text }}</text>

          <!-- 日程信息 -->
          <view v-if="action.action_type === 'schedule' && action.scheduled_date" class="action-schedule">
            <text class="schedule-icon">📅</text>
            <text class="schedule-text">
              {{ action.scheduled_date }}
              <text v-if="action.scheduled_time"> {{ action.scheduled_time }}</text>
            </text>
          </view>

          <!-- 底部信息栏 -->
          <view class="action-footer">
            <!-- 时间记录 -->
            <view class="time-log" @click.stop="showTimeLog(action)">
              <text class="time-icon">⏱</text>
              <text class="time-text">
                {{ action.time_spent_minutes ? action.time_spent_minutes + '分钟' : '记录时间' }}
              </text>
            </view>

            <!-- 积分 -->
            <text v-if="action.reward_points" class="action-points">+{{ action.reward_points }}分</text>

            <!-- 完成按钮 -->
            <button
              v-if="canComplete(action)"
              class="complete-btn"
              size="mini"
              @click.stop="handleComplete(action.id)"
            >
              完成
            </button>
          </view>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="actionStore.loading" class="loading-state">
        <text>加载中...</text>
      </view>
    </scroll-view>

    <!-- 时间记录弹窗 -->
    <view v-if="timeLogVisible" class="modal-mask" @click="timeLogVisible = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">记录时间</text>
        <view class="time-input-row">
          <input
            v-model="timeMinutesStr"
            class="time-input"
            type="number"
            placeholder="请输入花费时间"
          />
          <text class="time-unit">分钟</text>
        </view>
        <view class="modal-actions">
          <button class="modal-cancel" @click="timeLogVisible = false">取消</button>
          <button class="modal-confirm" @click="confirmTimeLog">确认</button>
        </view>
      </view>
    </view>

    <!-- 创建按钮 -->
    <view class="fab-btn" @click="goCreate">
      <text class="fab-icon">+</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useActionStore } from '@/stores/action'
import type { ActionItem } from '@/services/types'

const actionStore = useActionStore()
const activeTab = ref<'todo' | 'schedule'>('todo')
const timeLogVisible = ref(false)
const timeMinutesStr = ref('')
const currentActionId = ref('')

const filteredActions = computed(() => {
  if (activeTab.value === 'todo') {
    return actionStore.todoActions
  }
  return actionStore.scheduleActions
})

onMounted(() => {
  actionStore.fetchActions()
})

function switchTab(tab: 'todo' | 'schedule') {
  activeTab.value = tab
}

function handleLoadMore() {
  actionStore.loadMore(activeTab.value)
}

function canComplete(action: ActionItem): boolean {
  return ['pending', 'in_progress', 'rejected'].includes(action.status)
}

async function handleComplete(id: string) {
  try {
    await actionStore.completeAction(id)
    uni.showToast({ title: '已标记完成', icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function showTimeLog(action: ActionItem) {
  currentActionId.value = action.id
  timeMinutesStr.value = action.time_spent_minutes ? String(action.time_spent_minutes) : ''
  timeLogVisible.value = true
}

async function confirmTimeLog() {
  const minutes = parseInt(timeMinutesStr.value)
  if (isNaN(minutes) || minutes < 0) {
    uni.showToast({ title: '请输入有效时间', icon: 'none' })
    return
  }

  try {
    await actionStore.updateTimeLog(currentActionId.value, minutes)
    timeLogVisible.value = false
    uni.showToast({ title: '记录成功', icon: 'success' })
  } catch {
    uni.showToast({ title: '记录失败', icon: 'none' })
  }
}

function goCreate() {
  uni.navigateTo({ url: '/pages/actions/create' })
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    submitted: '待审核',
    approved: '已完成',
    rejected: '已驳回',
  }
  return map[status] || status
}
</script>

<style lang="scss" scoped>
.action-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f6fa;
}

.tab-bar {
  display: flex;
  background: #fff;
  padding: 0 32rpx;
  border-bottom: 1rpx solid #eee;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 24rpx 0;
  font-size: 28rpx;
  color: #666;
  position: relative;

  &.active {
    color: #4a90d9;
    font-weight: 600;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 48rpx;
      height: 4rpx;
      background: #4a90d9;
      border-radius: 2rpx;
    }
  }
}

.action-list {
  flex: 1;
  padding: 24rpx;
}

.action-card {
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.action-cover {
  width: 100%;
  height: 200rpx;
}

.action-info {
  padding: 24rpx;
}

.action-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.action-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-status {
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  background: #f0f0f0;
  color: #666;
  margin-left: 16rpx;
  flex-shrink: 0;

  &.status-pending {
    background: #f0f0f0;
    color: #666;
  }

  &.status-in_progress {
    background: #e6f7ff;
    color: #1890ff;
  }

  &.status-submitted {
    background: #fff7e6;
    color: #fa8c16;
  }

  &.status-approved {
    background: #f6ffed;
    color: #52c41a;
  }

  &.status-rejected {
    background: #fff1f0;
    color: #f5222d;
  }
}

.action-desc {
  font-size: 26rpx;
  color: #666;
  display: block;
  margin-bottom: 12rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-schedule {
  display: flex;
  align-items: center;
  margin-bottom: 12rpx;
}

.schedule-icon {
  font-size: 24rpx;
  margin-right: 8rpx;
}

.schedule-text {
  font-size: 24rpx;
  color: #4a90d9;
}

.action-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8rpx;
}

.time-log {
  display: flex;
  align-items: center;
  padding: 8rpx 16rpx;
  background: #f5f6fa;
  border-radius: 8rpx;
}

.time-icon {
  font-size: 24rpx;
  margin-right: 6rpx;
}

.time-text {
  font-size: 24rpx;
  color: #666;
}

.action-points {
  font-size: 24rpx;
  color: #52c41a;
  font-weight: 500;
}

.complete-btn {
  background: #4a90d9;
  color: #fff;
  font-size: 24rpx;
  border-radius: 8rpx;
  padding: 8rpx 24rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 32rpx;
}

.create-btn {
  background: #4a90d9;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
  padding: 16rpx 48rpx;
}

.loading-state {
  text-align: center;
  padding: 32rpx;
  color: #999;
  font-size: 26rpx;
}

/* 时间记录弹窗 */
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

.time-input-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 32rpx;
}

.time-input {
  flex: 1;
  height: 80rpx;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.time-unit {
  font-size: 28rpx;
  color: #666;
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

.fab-btn {
  position: fixed;
  right: 40rpx;
  bottom: 120rpx;
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: #4a90d9;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(74, 144, 217, 0.4);
}

.fab-icon {
  font-size: 48rpx;
  color: #fff;
  line-height: 1;
}
</style>
