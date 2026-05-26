<template>
  <view class="preferences-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">饮食偏好设置</text>
      <view class="nav-right">
        <text class="save-link" @click="handleSave">保存</text>
      </view>
    </view>

    <scroll-view class="content" scroll-y>
      <!-- 口味偏好 -->
      <view class="section-card">
        <view class="section-header">
          <text class="section-icon">🌶️</text>
          <text class="section-title">口味偏好</text>
        </view>
        <text class="section-desc">选择家庭成员喜欢的口味</text>
        <view class="tag-grid">
          <view
            v-for="taste in availableTastes"
            :key="taste"
            class="tag-item"
            :class="{ active: selectedTastes.includes(taste) }"
            @click="toggleTaste(taste)"
          >
            <text>{{ taste }}</text>
          </view>
        </view>
      </view>

      <!-- 喜好食材 -->
      <view class="section-card">
        <view class="section-header">
          <text class="section-icon">💚</text>
          <text class="section-title">喜好食材</text>
        </view>
        <text class="section-desc">经常想吃的食材</text>
        <view class="list-input-area">
          <view class="list-items">
            <view
              v-for="(item, idx) in favorites"
              :key="idx"
              class="list-item"
            >
              <text class="item-text">{{ item }}</text>
              <text class="remove-btn" @click="removeFavorite(idx)">✕</text>
            </view>
          </view>
          <view class="add-input-row">
            <input
              v-model="newFavorite"
              class="add-input"
              placeholder="添加喜好食材"
              @confirm="addFavorite"
            />
            <view class="add-btn" @click="addFavorite">
              <text>添加</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 禁忌食材 -->
      <view class="section-card">
        <view class="section-header">
          <text class="section-icon">🚫</text>
          <text class="section-title">禁忌食材</text>
        </view>
        <text class="section-desc">过敏或不喜欢的食材</text>
        <view class="list-input-area">
          <view class="list-items">
            <view
              v-for="(item, idx) in restrictions"
              :key="idx"
              class="list-item restriction"
            >
              <text class="item-text">{{ item }}</text>
              <text class="remove-btn" @click="removeRestriction(idx)">✕</text>
            </view>
          </view>
          <view class="add-input-row">
            <input
              v-model="newRestriction"
              class="add-input"
              placeholder="添加禁忌食材"
              @confirm="addRestriction"
            />
            <view class="add-btn restriction-add" @click="addRestriction">
              <text>添加</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部间距 -->
      <view class="bottom-spacer"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const availableTastes = [
  '清淡', '麻辣', '酸甜', '咸鲜', '香辣',
  '酱香', '蒜香', '葱香', '甜品', '烧烤',
  '卤味', '凉拌', '蒸煮', '煲汤', '快炒',
]

const selectedTastes = ref<string[]>([])
const favorites = ref<string[]>([])
const restrictions = ref<string[]>([])
const newFavorite = ref('')
const newRestriction = ref('')

function toggleTaste(taste: string) {
  const idx = selectedTastes.value.indexOf(taste)
  if (idx >= 0) {
    selectedTastes.value.splice(idx, 1)
  } else {
    selectedTastes.value.push(taste)
  }
}

function addFavorite() {
  const val = newFavorite.value.trim()
  if (val && !favorites.value.includes(val)) {
    favorites.value.push(val)
    newFavorite.value = ''
  }
}

function removeFavorite(idx: number) {
  favorites.value.splice(idx, 1)
}

function addRestriction() {
  const val = newRestriction.value.trim()
  if (val && !restrictions.value.includes(val)) {
    restrictions.value.push(val)
    newRestriction.value = ''
  }
}

function removeRestriction(idx: number) {
  restrictions.value.splice(idx, 1)
}

function handleSave() {
  const prefs = {
    tastes: selectedTastes.value,
    favorites: favorites.value,
    restrictions: restrictions.value,
  }
  uni.setStorageSync('diet_preferences', JSON.stringify(prefs))
  uni.showToast({ title: '保存成功', icon: 'success' })
  setTimeout(() => uni.navigateBack(), 800)
}

function loadPreferences() {
  try {
    const stored = uni.getStorageSync('diet_preferences')
    if (stored) {
      const prefs = JSON.parse(stored)
      selectedTastes.value = prefs.tastes || []
      favorites.value = prefs.favorites || []
      restrictions.value = prefs.restrictions || []
    }
  } catch {
    // ignore
  }
}

function goBack() {
  uni.navigateBack()
}

onMounted(() => {
  loadPreferences()
})
</script>

<style lang="scss" scoped>
.preferences-page {
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
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
  width: 64rpx;
  display: flex;
  justify-content: flex-end;
}

.save-link {
  font-size: 28rpx;
  color: #fff;
}

.content {
  flex: 1;
  padding: 24rpx 32rpx;
}

.section-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.section-icon {
  font-size: 36rpx;
  margin-right: 12rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.section-desc {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 20rpx;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.tag-item {
  padding: 14rpx 28rpx;
  background: #f5f6fa;
  border-radius: 32rpx;
  font-size: 26rpx;
  color: #666;
  border: 1rpx solid #e8e8e8;
  transition: all 0.2s;

  &.active {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: #fff;
    border-color: transparent;
  }
}

.list-input-area {
  margin-top: 8rpx;
}

.list-items {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.list-item {
  display: flex;
  align-items: center;
  padding: 10rpx 20rpx;
  background: #e6f7ff;
  border-radius: 24rpx;
  border: 1rpx solid #91d5ff;

  &.restriction {
    background: #fff1f0;
    border-color: #ffa39e;
  }
}

.item-text {
  font-size: 26rpx;
  color: #333;
  margin-right: 8rpx;
}

.remove-btn {
  font-size: 24rpx;
  color: #999;
}

.add-input-row {
  display: flex;
  gap: 12rpx;
}

.add-input {
  flex: 1;
  height: 68rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
  padding: 0 20rpx;
  font-size: 26rpx;
  border: 1rpx solid #e8e8e8;
}

.add-btn {
  height: 68rpx;
  padding: 0 28rpx;
  background: #4a90d9;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  color: #fff;

  &.restriction-add {
    background: #f5222d;
  }
}

.bottom-spacer {
  height: 48rpx;
}
</style>
