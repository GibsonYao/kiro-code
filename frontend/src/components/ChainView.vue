<template>
  <scroll-view class="chain-view" scroll-y>
    <!-- 愿望层级 -->
    <view v-if="chainData.wish" class="chain-level">
      <view class="level-header">
        <view class="level-icon wish-icon">✨</view>
        <text class="level-label">愿望</text>
      </view>
      <view class="level-connector"></view>
      <view class="chain-card wish-card">
        <view class="chain-card-image" v-if="chainData.wish.vision_image_url || chainData.wish.cover_image_url">
          <image
            :src="chainData.wish.vision_image_url || chainData.wish.cover_image_url"
            mode="aspectFill"
            class="card-img"
          />
        </view>
        <view v-else class="chain-card-placeholder wish-placeholder">
          <text class="placeholder-icon">✨</text>
        </view>
        <view class="chain-card-body">
          <text class="chain-card-title">{{ chainData.wish.display_text || chainData.wish.title }}</text>
          <text v-if="chainData.wish.vision_story" class="chain-card-desc">
            {{ chainData.wish.vision_story.slice(0, 80) }}{{ chainData.wish.vision_story.length > 80 ? '...' : '' }}
          </text>
          <view class="chain-card-status">
            <text class="status-badge" :class="chainData.wish.status">{{ statusLabel(chainData.wish.status) }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 目标层级 -->
    <view class="chain-level">
      <view class="level-header">
        <view class="level-icon goal-icon">🎯</view>
        <text class="level-label">目标</text>
      </view>
      <view class="level-connector"></view>
      <view class="chain-card goal-card">
        <view class="chain-card-image" v-if="chainData.goal.cover_image_url">
          <image
            :src="chainData.goal.cover_image_url"
            mode="aspectFill"
            class="card-img"
          />
        </view>
        <view v-else class="chain-card-placeholder goal-placeholder">
          <text class="placeholder-icon">🎯</text>
        </view>
        <view class="chain-card-body">
          <text class="chain-card-title">{{ chainData.goal.display_text || chainData.goal.title }}</text>
          <text v-if="chainData.goal.smart_specific" class="chain-card-desc">
            {{ chainData.goal.smart_specific }}
          </text>
          <!-- 进度 -->
          <view class="chain-progress">
            <view class="progress-bar">
              <view class="progress-fill" :style="{ width: chainData.goal.progress + '%' }"></view>
            </view>
            <text class="progress-text">{{ chainData.goal.progress }}%</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 计划层级 -->
    <view v-if="chainData.plans.length > 0" class="chain-level">
      <view class="level-header">
        <view class="level-icon plan-icon">📋</view>
        <text class="level-label">计划 ({{ chainData.plans.length }})</text>
      </view>
      <view class="level-connector"></view>
      <view class="chain-cards-list">
        <view v-for="plan in chainData.plans" :key="plan.id" class="chain-card plan-card">
          <view class="chain-card-image" v-if="plan.cover_image_url">
            <image :src="plan.cover_image_url" mode="aspectFill" class="card-img" />
          </view>
          <view v-else class="chain-card-placeholder plan-placeholder">
            <text class="placeholder-icon">📋</text>
          </view>
          <view class="chain-card-body">
            <text class="chain-card-title">{{ plan.display_text || plan.title }}</text>
            <view class="plan-meta">
              <text v-if="plan.start_date" class="meta-text">
                {{ plan.start_date }} ~ {{ plan.end_date || '未定' }}
              </text>
              <text class="status-badge" :class="plan.status">{{ planStatusLabel(plan.status) }}</text>
            </view>

            <!-- 步骤列表 -->
            <view v-if="plan.steps.length > 0" class="steps-list">
              <view v-for="step in plan.steps" :key="step.id" class="step-item">
                <view class="step-dot" :class="step.status"></view>
                <text class="step-title">{{ step.title }}</text>
                <text v-if="step.is_bounty" class="bounty-tag">悬赏</text>
              </view>
            </view>

            <!-- 关联任务 -->
            <view v-if="plan.tasks.length > 0" class="nested-section">
              <view class="nested-header">
                <view class="level-icon task-icon small">📌</view>
                <text class="nested-label">任务 ({{ plan.tasks.length }})</text>
              </view>
              <view v-for="task in plan.tasks" :key="task.id" class="nested-card">
                <view class="nested-card-body">
                  <text class="nested-card-title">{{ task.display_text || task.title }}</text>
                  <view class="task-meta">
                    <text class="points-badge reward">+{{ task.reward_points }}</text>
                    <text v-if="task.penalty_points > 0" class="points-badge penalty">-{{ task.penalty_points }}</text>
                    <text class="status-badge small" :class="task.status">{{ statusLabel(task.status) }}</text>
                  </view>

                  <!-- 关联行动 -->
                  <view v-if="task.actions.length > 0" class="actions-list">
                    <view v-for="action in task.actions" :key="action.id" class="action-item">
                      <text class="action-type-icon">{{ action.action_type === 'todo' ? '☑️' : '📅' }}</text>
                      <text class="action-title">{{ action.display_text || action.title }}</text>
                      <text class="status-dot" :class="action.status"></text>
                    </view>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 无计划提示 -->
    <view v-else class="empty-level">
      <text class="empty-level-text">暂无关联计划</text>
      <text class="empty-level-hint">创建计划并关联此目标，即可在此查看完整链路</text>
    </view>

    <!-- 底部安全区 -->
    <view class="safe-bottom"></view>
  </scroll-view>
</template>

<script setup lang="ts">
import type { GoalChainResponse } from '@/services/types'

interface Props {
  chainData: GoalChainResponse
}

defineProps<Props>()

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    active: '进行中',
    completed: '已完成',
    archived: '已归档',
    achieved: '已达成',
    draft: '草稿',
    overdue: '已过期',
    pending: '待处理',
    in_progress: '进行中',
    submitted: '已提交',
    approved: '已通过',
    rejected: '已驳回',
    claimed: '已认领',
    expired: '已过期',
  }
  return map[status] || status
}

function planStatusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '进行中',
    completed: '已完成',
    overdue: '已过期',
  }
  return map[status] || status
}
</script>

<style lang="scss" scoped>
.chain-view {
  padding: 32rpx;
  height: 100%;
}

// 链路层级
.chain-level {
  margin-bottom: 8rpx;
}

.level-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.level-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;

  &.wish-icon { background: #fff3e0; }
  &.goal-icon { background: #e8f5e9; }
  &.plan-icon { background: #e3f2fd; }
  &.task-icon { background: #fce4ec; }
  &.small { width: 40rpx; height: 40rpx; font-size: 20rpx; border-radius: 10rpx; }
}

.level-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.level-connector {
  width: 4rpx;
  height: 24rpx;
  background: linear-gradient(180deg, #667eea, #764ba2);
  margin-left: 26rpx;
  margin-bottom: 16rpx;
  border-radius: 2rpx;
}

// 链路卡片
.chain-card {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 24rpx;
}

.chain-card-image {
  width: 100%;
  height: 200rpx;
  overflow: hidden;
}

.card-img {
  width: 100%;
  height: 100%;
}

// 占位图
.chain-card-placeholder {
  width: 100%;
  height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.wish-placeholder { background: linear-gradient(135deg, #fff3e0, #ffe0b2); }
  &.goal-placeholder { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); }
  &.plan-placeholder { background: linear-gradient(135deg, #e3f2fd, #bbdefb); }
}

.placeholder-icon {
  font-size: 56rpx;
  opacity: 0.6;
}

.chain-card-body {
  padding: 20rpx 24rpx 24rpx;
}

.chain-card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8rpx;
  display: block;
}

.chain-card-desc {
  font-size: 24rpx;
  color: #666;
  line-height: 1.5;
  margin-bottom: 12rpx;
  display: block;
}

.chain-card-status {
  margin-top: 8rpx;
}

// 进度条
.chain-progress {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 12rpx;
}

.progress-bar {
  flex: 1;
  height: 14rpx;
  background: #f0f0f0;
  border-radius: 7rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #43e97b, #38f9d7);
  border-radius: 7rpx;
}

.progress-text {
  font-size: 24rpx;
  color: #666;
  font-weight: 600;
}

// 状态标签
.status-badge {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  display: inline-block;

  &.active { background: #e8f5e9; color: #2e7d32; }
  &.completed { background: #e3f2fd; color: #1565c0; }
  &.achieved { background: #e8f5e9; color: #2e7d32; }
  &.archived { background: #f5f5f5; color: #9e9e9e; }
  &.draft { background: #fff3e0; color: #e65100; }
  &.overdue { background: #fce4ec; color: #c62828; }
  &.pending { background: #f5f5f5; color: #757575; }
  &.in_progress { background: #e8f5e9; color: #2e7d32; }
  &.submitted { background: #e3f2fd; color: #1565c0; }
  &.approved { background: #e8f5e9; color: #2e7d32; }
  &.rejected { background: #fce4ec; color: #c62828; }
  &.claimed { background: #fff3e0; color: #e65100; }
  &.expired { background: #f5f5f5; color: #9e9e9e; }
  &.small { font-size: 20rpx; padding: 2rpx 12rpx; }
}

// 计划元信息
.plan-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 8rpx;
}

.meta-text {
  font-size: 22rpx;
  color: #999;
}

// 步骤列表
.steps-list {
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #f5f5f5;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 8rpx 0;
}

.step-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #e0e0e0;

  &.completed { background: #43e97b; }
  &.in_progress { background: #667eea; }
}

.step-title {
  font-size: 24rpx;
  color: #555;
  flex: 1;
}

.bounty-tag {
  font-size: 20rpx;
  color: #ff9800;
  background: #fff3e0;
  padding: 2rpx 10rpx;
  border-radius: 8rpx;
}

// 嵌套区域（任务）
.nested-section {
  margin-top: 20rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #f5f5f5;
}

.nested-header {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 12rpx;
}

.nested-label {
  font-size: 24rpx;
  font-weight: 600;
  color: #555;
}

.nested-card {
  background: #fafafa;
  border-radius: 12rpx;
  margin-bottom: 12rpx;
  overflow: hidden;
}

.nested-card-body {
  padding: 16rpx 20rpx;
}

.nested-card-title {
  font-size: 26rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 8rpx;
  display: block;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-wrap: wrap;
}

.points-badge {
  font-size: 20rpx;
  padding: 2rpx 10rpx;
  border-radius: 8rpx;
  font-weight: 600;

  &.reward { background: #e8f5e9; color: #2e7d32; }
  &.penalty { background: #fce4ec; color: #c62828; }
}

// 行动列表
.actions-list {
  margin-top: 12rpx;
  padding-top: 12rpx;
  border-top: 1rpx dashed #e0e0e0;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 6rpx 0;
}

.action-type-icon {
  font-size: 22rpx;
}

.action-title {
  font-size: 22rpx;
  color: #666;
  flex: 1;
}

.status-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #e0e0e0;

  &.approved { background: #43e97b; }
  &.in_progress { background: #667eea; }
  &.submitted { background: #ffa726; }
  &.pending { background: #e0e0e0; }
}

// 卡片列表
.chain-cards-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

// 空状态
.empty-level {
  text-align: center;
  padding: 48rpx;
  background: #fff;
  border-radius: 20rpx;
  margin-top: 16rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.empty-level-text {
  font-size: 28rpx;
  color: #999;
  display: block;
  margin-bottom: 8rpx;
}

.empty-level-hint {
  font-size: 24rpx;
  color: #ccc;
}

.safe-bottom {
  height: calc(32rpx + env(safe-area-inset-bottom));
}
</style>
