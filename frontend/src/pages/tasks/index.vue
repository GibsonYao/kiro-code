<template>
  <view class="task-page">
    <!-- Tab切换：我的任务 / 悬赏任务 -->
    <view class="tab-bar">
      <view
        class="tab-item"
        :class="{ active: activeTab === 'my' }"
        @click="switchTab('my')"
      >
        我的任务
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'bounty' }"
        @click="switchTab('bounty')"
      >
        悬赏任务
      </view>
    </view>

    <!-- 任务列表 -->
    <scroll-view
      class="task-list"
      scroll-y
      @scrolltolower="loadMore"
    >
      <!-- 我的任务 -->
      <template v-if="activeTab === 'my'">
        <view v-if="taskStore.isEmpty" class="empty-state">
          <text class="empty-text">暂无任务</text>
          <button class="create-btn" @click="goCreate">创建任务</button>
        </view>
        <view
          v-for="task in taskStore.myTasks"
          :key="task.id"
          class="task-card"
          @click="goDetail(task.id)"
        >
          <image
            v-if="task.cover_image_url"
            :src="task.cover_image_url"
            class="task-cover"
            mode="aspectFill"
          />
          <view class="task-info">
            <text class="task-title">{{ task.title }}</text>
            <text class="task-desc">{{ task.display_text || task.description || '' }}</text>
            <view class="task-meta">
              <view class="task-status" :class="'status-' + task.status">
                {{ statusLabel(task.status) }}
              </view>
              <view class="task-points">
                <text v-if="task.reward_points" class="points-reward">+{{ task.reward_points }}分</text>
                <text v-if="task.penalty_points" class="points-penalty">-{{ task.penalty_points }}分</text>
              </view>
            </view>
          </view>
        </view>
      </template>

      <!-- 悬赏任务 -->
      <template v-if="activeTab === 'bounty'">
        <view v-if="taskStore.bountyTasks.length === 0 && !taskStore.loading" class="empty-state">
          <text class="empty-text">暂无可认领的悬赏任务</text>
        </view>
        <view
          v-for="task in taskStore.bountyTasks"
          :key="task.id"
          class="task-card bounty-card"
        >
          <image
            v-if="task.cover_image_url"
            :src="task.cover_image_url"
            class="task-cover"
            mode="aspectFill"
          />
          <view class="task-info">
            <text class="task-title">{{ task.title }}</text>
            <text class="task-desc">{{ task.display_text || task.description || '' }}</text>
            <view class="task-meta">
              <view class="task-points">
                <text v-if="task.reward_points" class="points-reward">奖励 +{{ task.reward_points }}分</text>
                <text v-if="task.time_limit_hours" class="time-limit">限时 {{ task.time_limit_hours }}h</text>
              </view>
              <button class="claim-btn" size="mini" @click.stop="handleClaim(task.id)">认领</button>
            </view>
          </view>
        </view>
      </template>

      <!-- 加载状态 -->
      <view v-if="taskStore.loading" class="loading-state">
        <text>加载中...</text>
      </view>
    </scroll-view>

    <!-- 创建按钮 -->
    <view class="fab-btn" @click="goCreate">
      <text class="fab-icon">+</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTaskStore } from '@/stores/task'

const taskStore = useTaskStore()
const activeTab = ref<'my' | 'bounty'>('my')

onMounted(() => {
  taskStore.fetchMyTasks()
})

function switchTab(tab: 'my' | 'bounty') {
  activeTab.value = tab
  if (tab === 'my') {
    taskStore.fetchMyTasks()
  } else {
    taskStore.fetchBountyTasks()
  }
}

function loadMore() {
  if (activeTab.value === 'my') {
    taskStore.loadMoreMyTasks()
  } else {
    taskStore.loadMoreBountyTasks()
  }
}

async function handleClaim(taskId: string) {
  try {
    await taskStore.claimTask(taskId)
    uni.showToast({ title: '认领成功', icon: 'success' })
  } catch {
    uni.showToast({ title: '认领失败', icon: 'none' })
  }
}

function goCreate() {
  uni.navigateTo({ url: '/pages/tasks/create' })
}

function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/tasks/detail?id=${id}` })
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待认领',
    claimed: '已认领',
    in_progress: '进行中',
    submitted: '待审核',
    approved: '已完成',
    rejected: '已驳回',
    expired: '已超时',
  }
  return map[status] || status
}
</script>

<style lang="scss" scoped>
.task-page {
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

.task-list {
  flex: 1;
  padding: 24rpx;
}

.task-card {
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.task-cover {
  width: 100%;
  height: 240rpx;
}

.task-info {
  padding: 24rpx;
}

.task-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.task-desc {
  font-size: 26rpx;
  color: #666;
  display: block;
  margin-bottom: 16rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-status {
  font-size: 24rpx;
  padding: 4rpx 16rpx;
  border-radius: 8rpx;
  background: #f0f0f0;
  color: #666;

  &.status-claimed,
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

  &.status-expired {
    background: #fff1f0;
    color: #f5222d;
  }
}

.task-points {
  display: flex;
  gap: 12rpx;
}

.points-reward {
  font-size: 24rpx;
  color: #52c41a;
}

.points-penalty {
  font-size: 24rpx;
  color: #f5222d;
}

.time-limit {
  font-size: 24rpx;
  color: #fa8c16;
}

.bounty-card {
  border-left: 6rpx solid #fa8c16;
}

.claim-btn {
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
