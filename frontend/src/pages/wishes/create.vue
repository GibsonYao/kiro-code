<template>
  <view class="wish-create-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">{{ isEdit ? '编辑愿望' : '创建愿望' }}</text>
      <view class="nav-right">
        <text
          v-if="isEdit"
          class="delete-btn"
          @click="handleDelete"
        >删除</text>
      </view>
    </view>

    <!-- 表单内容 -->
    <view class="form-container">
      <!-- 标题输入 -->
      <view class="form-section">
        <text class="section-label">愿望标题</text>
        <view class="input-wrapper">
          <input
            v-model="title"
            class="title-input"
            placeholder="描述你的愿望..."
            maxlength="256"
            :focus="!isEdit"
          />
          <text class="char-count">{{ title.length }}/256</text>
        </view>
        <text class="section-hint">输入愿望标题后，AI将自动生成愿景故事和愿景图</text>
      </view>

      <!-- AI生成状态展示（编辑模式） -->
      <view v-if="isEdit && currentWish" class="ai-section">
        <text class="section-label">AI愿景</text>

        <!-- 愿景图 -->
        <view class="vision-image-container">
          <image
            v-if="currentWish.vision_image_url"
            class="vision-image"
            :src="currentWish.vision_image_url"
            mode="widthFix"
          />
          <view v-else class="vision-generating">
            <view class="generating-animation">
              <text class="generating-dot">●</text>
              <text class="generating-dot delay-1">●</text>
              <text class="generating-dot delay-2">●</text>
            </view>
            <text class="generating-text">AI正在生成愿景图...</text>
          </view>
        </view>

        <!-- 愿景故事 -->
        <view class="vision-story-container">
          <text class="story-label">愿景故事</text>
          <view v-if="currentWish.vision_story" class="story-content">
            <text class="story-text">{{ currentWish.vision_story }}</text>
          </view>
          <view v-else class="story-generating">
            <text class="generating-text">AI正在生成愿景故事...</text>
          </view>
        </view>

        <!-- 重新生成按钮 -->
        <view class="regenerate-section">
          <view
            class="regenerate-btn"
            :class="{ disabled: regenerating }"
            @click="handleRegenerate"
          >
            <text class="regenerate-icon">🔄</text>
            <text class="regenerate-text">
              {{ regenerating ? '重新生成中...' : '重新生成愿景' }}
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部操作栏 -->
    <view class="bottom-bar">
      <view
        class="submit-btn"
        :class="{ disabled: !canSubmit || submitting }"
        @click="handleSubmit"
      >
        <text class="submit-text">
          {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '创建愿望') }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useWishStore } from '@/stores/wish'
import { wishApi } from '@/services/api/wishes'
import type { WishItem } from '@/services/types'

const wishStore = useWishStore()

// 页面状态
const title = ref('')
const isEdit = ref(false)
const wishId = ref('')
const currentWish = ref<WishItem | null>(null)
const submitting = ref(false)
const regenerating = ref(false)

// 计算属性
const canSubmit = computed(() => title.value.trim().length > 0)

// 页面加载
onLoad((query) => {
  const id = query?.id
  if (id) {
    isEdit.value = true
    wishId.value = id
    loadWish(id)
  }
})

/** 加载愿望详情 */
async function loadWish(id: string): Promise<void> {
  try {
    const wish = await wishApi.getWish(id)
    currentWish.value = wish
    title.value = wish.title
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
    setTimeout(() => goBack(), 1500)
  }
}

/** 提交表单 */
async function handleSubmit(): Promise<void> {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    if (isEdit.value) {
      // 编辑模式
      const wish = await wishStore.updateWish(wishId.value, { title: title.value.trim() })
      currentWish.value = wish
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      // 创建模式
      const wish = await wishStore.createWish(title.value.trim())
      uni.showToast({ title: '创建成功', icon: 'success' })
      // 跳转到编辑页面查看AI生成状态
      const newId = String(wish.id)
      setTimeout(() => {
        uni.redirectTo({ url: `/pages/wishes/create?id=${newId}` })
      }, 1000)
    }
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

/** 重新生成愿景 */
async function handleRegenerate(): Promise<void> {
  if (regenerating.value) return

  regenerating.value = true
  try {
    const wish = await wishStore.regenerateVision(wishId.value)
    currentWish.value = wish
    uni.showToast({ title: '已触发重新生成', icon: 'success' })
    // 延迟刷新以获取最新生成结果
    setTimeout(() => loadWish(wishId.value), 3000)
  } catch {
    uni.showToast({ title: '重新生成失败', icon: 'none' })
  } finally {
    regenerating.value = false
  }
}

/** 删除愿望 */
async function handleDelete(): Promise<void> {
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，确定要删除这个愿望吗？',
    confirmColor: '#ff4444',
    success: async (res) => {
      if (res.confirm) {
        try {
          await wishStore.deleteWish(wishId.value)
          uni.showToast({ title: '已删除', icon: 'success' })
          setTimeout(() => goBack(), 1000)
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
}

/** 返回上一页 */
function goBack(): void {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.wish-create-page {
  min-height: 100vh;
  background-color: #f5f6fa;
  padding-bottom: 140rpx;
}

// 导航栏
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}

.nav-back {
  padding: 12rpx;
}

.back-icon {
  font-size: 36rpx;
  color: #333;
}

.nav-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a1a2e;
}

.nav-right {
  min-width: 80rpx;
  text-align: right;
}

.delete-btn {
  font-size: 28rpx;
  color: #ff4444;
}

// 表单
.form-container {
  padding: 32rpx;
}

.form-section {
  margin-bottom: 40rpx;
}

.section-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
  display: block;
}

.section-hint {
  font-size: 24rpx;
  color: #999;
  margin-top: 12rpx;
  display: block;
}

.input-wrapper {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.title-input {
  width: 100%;
  font-size: 32rpx;
  color: #333;
  margin-bottom: 8rpx;
}

.char-count {
  font-size: 22rpx;
  color: #ccc;
  text-align: right;
  display: block;
}

// AI生成区域
.ai-section {
  margin-top: 40rpx;
}

.vision-image-container {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.vision-image {
  width: 100%;
  display: block;
}

.vision-generating {
  height: 320rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.generating-animation {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.generating-dot {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  animation: pulse 1.4s infinite;

  &.delay-1 { animation-delay: 0.2s; }
  &.delay-2 { animation-delay: 0.4s; }
}

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}

.generating-text {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}

// 愿景故事
.vision-story-container {
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.story-label {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 12rpx;
  display: block;
}

.story-content {
  padding: 16rpx;
  background: #f8f9ff;
  border-radius: 12rpx;
  border-left: 6rpx solid #667eea;
}

.story-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.8;
}

.story-generating {
  padding: 24rpx;
  text-align: center;
}

// 重新生成
.regenerate-section {
  display: flex;
  justify-content: center;
}

.regenerate-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 16rpx 32rpx;
  background: #f0f2ff;
  border-radius: 32rpx;
  transition: opacity 0.2s;

  &.disabled {
    opacity: 0.5;
  }
}

.regenerate-icon {
  font-size: 28rpx;
}

.regenerate-text {
  font-size: 26rpx;
  color: #667eea;
}

// 底部操作栏
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.4);

  &.disabled {
    opacity: 0.5;
    box-shadow: none;
  }
}

.submit-text {
  font-size: 30rpx;
  color: #fff;
  font-weight: 600;
}
</style>
