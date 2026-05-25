<template>
  <view class="goal-create-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">{{ isEdit ? '编辑目标' : '创建目标' }}</text>
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
        <text class="section-label">目标标题</text>
        <view class="input-wrapper">
          <input
            v-model="title"
            class="title-input"
            placeholder="输入你的目标..."
            maxlength="256"
            :focus="!isEdit"
          />
          <text class="char-count">{{ title.length }}/256</text>
        </view>
      </view>

      <!-- 描述输入 -->
      <view class="form-section">
        <text class="section-label">目标描述</text>
        <view class="input-wrapper textarea-wrapper">
          <textarea
            v-model="description"
            class="desc-input"
            placeholder="详细描述你的目标（可选）..."
            maxlength="2000"
            :auto-height="true"
          />
          <text class="char-count">{{ description.length }}/2000</text>
        </view>
        <text class="section-hint">AI将基于标题和描述生成SMART目标描述和配图</text>
      </view>

      <!-- 关联愿望选择 -->
      <view class="form-section">
        <text class="section-label">关联愿望（可选）</text>
        <view class="wish-selector" @click="showWishPicker = true">
          <text v-if="selectedWish" class="wish-selected">{{ selectedWish.title }}</text>
          <text v-else class="wish-placeholder">选择关联的愿望...</text>
          <text class="wish-arrow">›</text>
        </view>
        <view v-if="selectedWish" class="wish-clear" @click="clearWish">
          <text class="clear-text">取消关联</text>
        </view>
      </view>

      <!-- AI生成状态展示（编辑模式） -->
      <view v-if="isEdit && currentGoal" class="ai-section">
        <text class="section-label">AI生成内容</text>

        <!-- 配图 -->
        <view class="cover-image-container">
          <image
            v-if="currentGoal.cover_image_url"
            class="cover-image"
            :src="currentGoal.cover_image_url"
            mode="widthFix"
          />
          <view v-else class="cover-generating">
            <view class="generating-animation">
              <text class="generating-dot">●</text>
              <text class="generating-dot delay-1">●</text>
              <text class="generating-dot delay-2">●</text>
            </view>
            <text class="generating-text">AI正在生成配图...</text>
          </view>
        </view>

        <!-- SMART描述 -->
        <view class="smart-section" v-if="currentGoal.smart_specific">
          <text class="smart-title">SMART目标分析</text>
          <view class="smart-list">
            <view class="smart-item">
              <view class="smart-badge">S</view>
              <view class="smart-detail">
                <text class="smart-label">具体性 (Specific)</text>
                <text class="smart-value">{{ currentGoal.smart_specific }}</text>
              </view>
            </view>
            <view class="smart-item">
              <view class="smart-badge measurable">M</view>
              <view class="smart-detail">
                <text class="smart-label">可衡量 (Measurable)</text>
                <text class="smart-value">{{ currentGoal.smart_measurable }}</text>
              </view>
            </view>
            <view class="smart-item">
              <view class="smart-badge achievable">A</view>
              <view class="smart-detail">
                <text class="smart-label">可达成 (Achievable)</text>
                <text class="smart-value">{{ currentGoal.smart_achievable }}</text>
              </view>
            </view>
            <view class="smart-item">
              <view class="smart-badge relevant">R</view>
              <view class="smart-detail">
                <text class="smart-label">相关性 (Relevant)</text>
                <text class="smart-value">{{ currentGoal.smart_relevant }}</text>
              </view>
            </view>
            <view class="smart-item">
              <view class="smart-badge time-bound">T</view>
              <view class="smart-detail">
                <text class="smart-label">时限性 (Time-bound)</text>
                <text class="smart-value">{{ currentGoal.smart_time_bound }}</text>
              </view>
            </view>
          </view>
        </view>
        <view v-else class="smart-generating">
          <text class="generating-text">AI正在生成SMART描述...</text>
        </view>
      </view>
    </view>

    <!-- 愿望选择弹窗 -->
    <view v-if="showWishPicker" class="picker-mask" @click="showWishPicker = false">
      <view class="picker-container" @click.stop>
        <view class="picker-header">
          <text class="picker-title">选择关联愿望</text>
          <text class="picker-close" @click="showWishPicker = false">✕</text>
        </view>
        <scroll-view class="picker-list" scroll-y>
          <view v-if="wishes.length === 0" class="picker-empty">
            <text>暂无愿望，请先创建愿望</text>
          </view>
          <view
            v-for="wish in wishes"
            :key="wish.id"
            class="picker-item"
            :class="{ selected: selectedWish?.id === wish.id }"
            @click="selectWish(wish)"
          >
            <text class="picker-item-title">{{ wish.title }}</text>
            <text v-if="selectedWish?.id === wish.id" class="picker-check">✓</text>
          </view>
        </scroll-view>
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
          {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '创建目标') }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useGoalStore } from '@/stores/goal'
import { goalApi } from '@/services/api/goals'
import { wishApi } from '@/services/api/wishes'
import type { GoalItem, WishItem } from '@/services/types'

const goalStore = useGoalStore()

// 页面状态
const title = ref('')
const description = ref('')
const isEdit = ref(false)
const goalId = ref('')
const currentGoal = ref<GoalItem | null>(null)
const submitting = ref(false)

// 愿望选择
const wishes = ref<WishItem[]>([])
const selectedWish = ref<WishItem | null>(null)
const showWishPicker = ref(false)

// 计算属性
const canSubmit = computed(() => title.value.trim().length > 0)

// 页面加载
onLoad((query) => {
  const id = query?.id
  if (id) {
    isEdit.value = true
    goalId.value = id
    loadGoal(id)
  }
})

onMounted(() => {
  loadWishes()
})

/** 加载愿望列表供选择 */
async function loadWishes(): Promise<void> {
  try {
    const res = await wishApi.getWishes({ page: 1, page_size: 100, status: 'active' })
    wishes.value = res.items
  } catch {
    // 静默失败，愿望选择非必须
  }
}

/** 加载目标详情 */
async function loadGoal(id: string): Promise<void> {
  try {
    const goal = await goalApi.getGoal(id)
    currentGoal.value = goal
    title.value = goal.title
    description.value = goal.description || ''
    // 如果有关联愿望，设置选中
    if (goal.wish_id) {
      const wishItem = wishes.value.find(w => w.id === goal.wish_id)
      if (wishItem) {
        selectedWish.value = wishItem
      }
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
    setTimeout(() => goBack(), 1500)
  }
}

/** 选择愿望 */
function selectWish(wish: WishItem): void {
  selectedWish.value = wish
  showWishPicker.value = false
}

/** 清除愿望关联 */
function clearWish(): void {
  selectedWish.value = null
}

/** 提交表单 */
async function handleSubmit(): Promise<void> {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    if (isEdit.value) {
      const goal = await goalStore.updateGoal(goalId.value, {
        title: title.value.trim(),
        description: description.value.trim() || undefined,
      })
      currentGoal.value = goal
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      const goal = await goalStore.createGoal({
        title: title.value.trim(),
        description: description.value.trim() || undefined,
        wish_id: selectedWish.value?.id,
      })
      uni.showToast({ title: '创建成功', icon: 'success' })
      // 跳转到编辑页面查看AI生成状态
      setTimeout(() => {
        uni.redirectTo({ url: `/pages/goals/create?id=${goal.id}` })
      }, 1000)
    }
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

/** 删除目标 */
async function handleDelete(): Promise<void> {
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，确定要删除这个目标吗？',
    confirmColor: '#ff4444',
    success: async (res) => {
      if (res.confirm) {
        try {
          await goalStore.deleteGoal(goalId.value)
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
.goal-create-page {
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

.textarea-wrapper {
  min-height: 160rpx;
}

.title-input {
  width: 100%;
  font-size: 32rpx;
  color: #333;
  margin-bottom: 8rpx;
}

.desc-input {
  width: 100%;
  font-size: 28rpx;
  color: #333;
  min-height: 120rpx;
  margin-bottom: 8rpx;
}

.char-count {
  font-size: 22rpx;
  color: #ccc;
  text-align: right;
  display: block;
}

// 愿望选择器
.wish-selector {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wish-selected {
  font-size: 28rpx;
  color: #333;
}

.wish-placeholder {
  font-size: 28rpx;
  color: #ccc;
}

.wish-arrow {
  font-size: 36rpx;
  color: #ccc;
}

.wish-clear {
  margin-top: 12rpx;
}

.clear-text {
  font-size: 24rpx;
  color: #ff4444;
}

// 愿望选择弹窗
.picker-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: flex-end;
}

.picker-container {
  width: 100%;
  max-height: 70vh;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 32rpx;
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.picker-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.picker-close {
  font-size: 32rpx;
  color: #999;
  padding: 8rpx;
}

.picker-list {
  max-height: 50vh;
}

.picker-empty {
  padding: 48rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
}

.picker-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 16rpx;
  border-bottom: 1rpx solid #f5f5f5;

  &.selected {
    background: #f0fff4;
  }
}

.picker-item-title {
  font-size: 28rpx;
  color: #333;
}

.picker-check {
  font-size: 28rpx;
  color: #43e97b;
  font-weight: 700;
}

// AI生成区域
.ai-section {
  margin-top: 40rpx;
}

.cover-image-container {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.cover-image {
  width: 100%;
  display: block;
}

.cover-generating {
  height: 280rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
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

// SMART描述
.smart-section {
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.smart-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

.smart-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.smart-item {
  display: flex;
  gap: 16rpx;
}

.smart-badge {
  width: 44rpx;
  height: 44rpx;
  border-radius: 12rpx;
  background: #43e97b;
  color: #fff;
  font-size: 24rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &.measurable { background: #667eea; }
  &.achievable { background: #f093fb; }
  &.relevant { background: #ffa726; }
  &.time-bound { background: #ef5350; }
}

.smart-detail {
  flex: 1;
}

.smart-label {
  font-size: 22rpx;
  color: #999;
  display: block;
  margin-bottom: 4rpx;
}

.smart-value {
  font-size: 26rpx;
  color: #333;
  line-height: 1.5;
}

.smart-generating {
  background: #fff;
  border-radius: 20rpx;
  padding: 48rpx;
  text-align: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
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
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  border-radius: 44rpx;
  box-shadow: 0 8rpx 24rpx rgba(67, 233, 123, 0.4);

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
