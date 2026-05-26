<template>
  <!-- 图文卡片组件 (Task 15.2) -->
  <view class="rich-card" :class="{ 'rich-card--loading': loading, 'rich-card--failed': failed }">
    <!-- 配图区域 -->
    <view class="rich-card__image-wrapper">
      <!-- 加载骨架屏 -->
      <view v-if="loading || isGenerating" class="rich-card__skeleton">
        <view class="rich-card__skeleton-shimmer" />
        <view class="rich-card__generating-tip">
          <text class="rich-card__generating-text">AI生成中...</text>
        </view>
      </view>

      <!-- 失败状态 -->
      <view v-else-if="failed" class="rich-card__failed-state">
        <text class="rich-card__failed-icon">⚠️</text>
        <text class="rich-card__failed-text">生成失败</text>
        <view class="rich-card__retry-btn" @tap="$emit('retry')">
          <text class="rich-card__retry-btn-text">点击重试</text>
        </view>
      </view>

      <!-- 实际图片 -->
      <image
        v-else-if="imageUrl"
        class="rich-card__image"
        :src="imageUrl"
        mode="aspectFill"
        :lazy-load="true"
        @error="onImageError"
      />

      <!-- 占位图 -->
      <view v-else class="rich-card__placeholder">
        <text class="rich-card__placeholder-icon">🎨</text>
      </view>

      <!-- 重试按钮（非失败状态下的重新生成） -->
      <view v-if="showRetry && !loading && !failed" class="rich-card__retry" @tap="$emit('retry')">
        <text class="rich-card__retry-text">重新生成</text>
      </view>
    </view>

    <!-- 内容区域 -->
    <view class="rich-card__content">
      <!-- 标题 -->
      <text class="rich-card__title">{{ title }}</text>

      <!-- AI生成的展示文案 -->
      <text v-if="displayText" class="rich-card__display-text">{{ displayText }}</text>

      <!-- 描述 -->
      <text v-if="description && !displayText" class="rich-card__description">{{ description }}</text>

      <!-- 底部插槽（状态标签、积分等） -->
      <view class="rich-card__footer">
        <slot name="footer" />
      </view>
    </view>

    <!-- 右上角状态标签 -->
    <view v-if="status" class="rich-card__badge" :class="`rich-card__badge--${statusType}`">
      <text class="rich-card__badge-text">{{ status }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAIStatusStore } from '@/stores/aiStatus'

const props = defineProps<{
  /** 卡片标题 */
  title: string
  /** AI生成的展示文案 */
  displayText?: string | null
  /** 原始描述 */
  description?: string | null
  /** 配图URL */
  imageUrl?: string | null
  /** 是否加载中 */
  loading?: boolean
  /** 是否生成失败 */
  failed?: boolean
  /** 是否显示重试按钮 */
  showRetry?: boolean
  /** 状态标签文字 */
  status?: string
  /** 状态类型（控制颜色） */
  statusType?: 'active' | 'completed' | 'pending' | 'warning' | 'error'
  /** 实体类型（用于检查AI生成状态） */
  entityType?: string
  /** 实体ID（用于检查AI生成状态） */
  entityId?: string
}>()

defineEmits<{
  retry: []
}>()

const aiStatusStore = useAIStatusStore()

/** 是否正在AI生成 */
const isGenerating = computed(() => {
  if (props.entityType && props.entityId) {
    return aiStatusStore.isGenerating(props.entityType, props.entityId)
  }
  return false
})

/** 图片加载失败处理 */
function onImageError() {
  // 图片加载失败时可以显示占位图
  console.warn('Image load failed:', props.imageUrl)
}
</script>

<style lang="scss" scoped>
.rich-card {
  background: #ffffff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 20rpx;
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:active {
    transform: scale(0.98);
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
  }

  &--loading {
    opacity: 0.8;
  }

  &--failed {
    .rich-card__image-wrapper {
      background: #fef2f2;
    }
  }
}

.rich-card__image-wrapper {
  width: 100%;
  height: 320rpx;
  position: relative;
  overflow: hidden;
  background: #f0f2f5;
}

.rich-card__image {
  width: 100%;
  height: 100%;
}

.rich-card__skeleton {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #f0f2f5 0%, #e8eaed 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.rich-card__skeleton-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

.rich-card__generating-tip {
  z-index: 1;
  padding: 12rpx 24rpx;
  background: rgba(74, 144, 217, 0.1);
  border-radius: 24rpx;
}

.rich-card__generating-text {
  font-size: 24rpx;
  color: #4a90d9;
}

.rich-card__placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.rich-card__placeholder-icon {
  font-size: 64rpx;
}

.rich-card__retry {
  position: absolute;
  bottom: 16rpx;
  right: 16rpx;
  padding: 8rpx 20rpx;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 20rpx;
}

.rich-card__retry-text {
  font-size: 22rpx;
  color: #ffffff;
}

.rich-card__content {
  padding: 24rpx;
}

.rich-card__title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1a1a2e;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rich-card__display-text {
  font-size: 26rpx;
  color: #4a5568;
  margin-top: 12rpx;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rich-card__description {
  font-size: 24rpx;
  color: #718096;
  margin-top: 12rpx;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rich-card__footer {
  margin-top: 16rpx;
}

.rich-card__badge {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  padding: 6rpx 16rpx;
  border-radius: 16rpx;
  z-index: 2;

  &--active {
    background: rgba(72, 187, 120, 0.9);
  }
  &--completed {
    background: rgba(74, 144, 217, 0.9);
  }
  &--pending {
    background: rgba(237, 137, 54, 0.9);
  }
  &--warning {
    background: rgba(245, 101, 101, 0.9);
  }
  &--error {
    background: rgba(160, 174, 192, 0.9);
  }
}

.rich-card__badge-text {
  font-size: 22rpx;
  color: #ffffff;
  font-weight: 500;
}

.rich-card__failed-state {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  gap: 12rpx;
}

.rich-card__failed-icon {
  font-size: 48rpx;
}

.rich-card__failed-text {
  font-size: 24rpx;
  color: #dc2626;
}

.rich-card__retry-btn {
  margin-top: 8rpx;
  padding: 12rpx 32rpx;
  background: #4a90d9;
  border-radius: 24rpx;
}

.rich-card__retry-btn-text {
  font-size: 24rpx;
  color: #ffffff;
  font-weight: 500;
}
</style>
