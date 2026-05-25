<template>
  <view class="review-page">
    <!-- 标题栏 -->
    <view class="page-header">
      <text class="header-title">待审核</text>
      <text class="header-count" v-if="reviewStore.total > 0">{{ reviewStore.total }}项</text>
    </view>

    <!-- 审核列表 -->
    <scroll-view
      class="review-list"
      scroll-y
      refresher-enabled
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <!-- 空状态 -->
      <view v-if="reviewStore.isEmpty" class="empty-state">
        <text class="empty-icon">✅</text>
        <text class="empty-text">暂无待审核项目</text>
        <text class="empty-hint">所有提交都已处理完毕</text>
      </view>

      <!-- 审核卡片 -->
      <view
        v-for="review in reviewStore.pendingReviews"
        :key="review.id"
        class="review-card"
      >
        <!-- 类型标签 -->
        <view class="card-header">
          <view class="target-tag" :class="'tag-' + review.target_type">
            {{ targetTypeLabel(review.target_type) }}
          </view>
          <text class="review-time">{{ formatTime(review.created_at) }}</text>
        </view>

        <!-- 证据内容 -->
        <view class="card-body">
          <text v-if="review.evidence_text" class="evidence-text">
            {{ review.evidence_text }}
          </text>

          <!-- 证据图片 -->
          <view v-if="review.evidence_photos && review.evidence_photos.length > 0" class="evidence-photos">
            <image
              v-for="(photo, idx) in review.evidence_photos"
              :key="idx"
              :src="photo"
              class="evidence-photo"
              mode="aspectFill"
              @click="previewImage(photo, review.evidence_photos!)"
            />
          </view>

          <text v-if="!review.evidence_text && (!review.evidence_photos || review.evidence_photos.length === 0)" class="no-evidence">
            无提交证据
          </text>
        </view>

        <!-- 操作按钮 -->
        <view class="card-actions">
          <button class="reject-btn" @click="openCommentModal(review.id, 'reject')">驳回</button>
          <button class="approve-btn" @click="openCommentModal(review.id, 'approve')">通过</button>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="reviewStore.loading && reviewStore.pendingReviews.length > 0" class="loading-state">
        <text>加载中...</text>
      </view>

      <!-- 没有更多 -->
      <view v-if="!reviewStore.hasMore && reviewStore.pendingReviews.length > 0" class="no-more">
        <text>没有更多了</text>
      </view>
    </scroll-view>

    <!-- 评论弹窗 -->
    <view v-if="modalVisible" class="modal-mask" @click="closeModal">
      <view class="modal-content" @click.stop>
        <text class="modal-title">{{ modalAction === 'approve' ? '审核通过' : '驳回审核' }}</text>
        <textarea
          v-model="commentText"
          class="comment-input"
          :placeholder="modalAction === 'approve' ? '添加备注（可选）' : '请输入驳回原因（可选）'"
          :maxlength="512"
        />
        <view class="modal-actions">
          <button class="modal-cancel" @click="closeModal">取消</button>
          <button
            class="modal-confirm"
            :class="{ 'confirm-reject': modalAction === 'reject' }"
            @click="confirmAction"
          >
            {{ modalAction === 'approve' ? '确认通过' : '确认驳回' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useReviewStore } from '@/stores/review'

const reviewStore = useReviewStore()

const isRefreshing = ref(false)
const modalVisible = ref(false)
const modalAction = ref<'approve' | 'reject'>('approve')
const currentReviewId = ref('')
const commentText = ref('')

onMounted(() => {
  reviewStore.fetchPendingReviews()
})

async function handleRefresh() {
  isRefreshing.value = true
  try {
    await reviewStore.fetchPendingReviews()
  } finally {
    isRefreshing.value = false
  }
}

function handleLoadMore() {
  reviewStore.loadMore()
}

function openCommentModal(id: string, action: 'approve' | 'reject') {
  currentReviewId.value = id
  modalAction.value = action
  commentText.value = ''
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
  commentText.value = ''
}

async function confirmAction() {
  const id = currentReviewId.value
  const comment = commentText.value.trim() || undefined

  try {
    if (modalAction.value === 'approve') {
      await reviewStore.approveReview(id, comment)
      uni.showToast({ title: '已通过', icon: 'success' })
    } else {
      await reviewStore.rejectReview(id, comment)
      uni.showToast({ title: '已驳回', icon: 'none' })
    }
    closeModal()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function targetTypeLabel(type: string): string {
  const map: Record<string, string> = {
    task: '任务',
    action: '行动',
  }
  return map[type] || type
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function previewImage(current: string, urls: string[]) {
  uni.previewImage({ current, urls })
}
</script>

<style lang="scss" scoped>
.review-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f6fa;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: #fff;
  border-bottom: 1rpx solid #eee;
}

.header-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.header-count {
  font-size: 26rpx;
  color: #999;
  background: #f0f0f0;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}

.review-list {
  flex: 1;
  padding: 24rpx;
}

.review-card {
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  border-bottom: 1rpx solid #f5f5f5;
}

.target-tag {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 8rpx;
  font-weight: 500;

  &.tag-task {
    background: #e6f7ff;
    color: #1890ff;
  }

  &.tag-action {
    background: #f6ffed;
    color: #52c41a;
  }
}

.review-time {
  font-size: 22rpx;
  color: #999;
}

.card-body {
  padding: 24rpx;
}

.evidence-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
  display: block;
  margin-bottom: 16rpx;
}

.evidence-photos {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.evidence-photo {
  width: 160rpx;
  height: 160rpx;
  border-radius: 8rpx;
}

.no-evidence {
  font-size: 26rpx;
  color: #999;
  font-style: italic;
}

.card-actions {
  display: flex;
  gap: 24rpx;
  padding: 20rpx 24rpx;
  border-top: 1rpx solid #f5f5f5;
}

.reject-btn {
  flex: 1;
  height: 72rpx;
  background: #fff1f0;
  color: #f5222d;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid #ffa39e;
}

.approve-btn {
  flex: 1;
  height: 72rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 160rpx 0;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 30rpx;
  color: #666;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 24rpx;
  color: #999;
}

.loading-state {
  text-align: center;
  padding: 32rpx;
  color: #999;
  font-size: 26rpx;
}

.no-more {
  text-align: center;
  padding: 32rpx;
  color: #ccc;
  font-size: 24rpx;
}

/* 评论弹窗 */
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
  width: 600rpx;
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

.comment-input {
  width: 100%;
  height: 200rpx;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
  margin-bottom: 32rpx;
  box-sizing: border-box;
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

  &.confirm-reject {
    background: #f5222d;
  }
}
</style>
