<template>
  <view class="guide-page">
    <!-- Swiper slides -->
    <swiper
      class="guide-swiper"
      :current="currentSlide"
      @change="onSlideChange"
      :indicator-dots="false"
    >
      <swiper-item v-for="(slide, index) in slides" :key="index">
        <view class="slide-content">
          <view class="slide-visual">
            <text class="slide-emoji">{{ slide.emoji }}</text>
          </view>
          <text class="slide-title">{{ slide.title }}</text>
          <text class="slide-desc">{{ slide.description }}</text>
        </view>
      </swiper-item>
    </swiper>

    <!-- Indicators -->
    <view class="indicators">
      <view
        v-for="(_, index) in slides"
        :key="index"
        class="indicator-dot"
        :class="{ active: currentSlide === index }"
      ></view>
    </view>

    <!-- Bottom actions -->
    <view class="bottom-actions">
      <view v-if="currentSlide < slides.length - 1" class="action-row">
        <text class="skip-btn" @click="finish">跳过</text>
        <view class="next-btn" @click="nextSlide">
          <text class="next-btn-text">下一步</text>
        </view>
      </view>
      <view v-else class="action-row center">
        <view class="start-btn" @click="finish">
          <text class="start-btn-text">开始使用</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const currentSlide = ref(0)

const slides = [
  {
    emoji: '💫',
    title: '许下愿望',
    description: '从一个小小的愿望开始，AI会帮你规划实现路径',
  },
  {
    emoji: '🎯',
    title: '拆解目标',
    description: 'AI智能拆解愿望为可执行的目标、计划和任务',
  },
  {
    emoji: '👨‍👩‍👧‍👦',
    title: '家庭协作',
    description: '全家人一起参与，互相激励，共同成长',
  },
  {
    emoji: '⭐',
    title: '积分激励',
    description: '完成任务获得积分奖励，让成长更有动力',
  },
]

function onSlideChange(e: { detail: { current: number } }) {
  currentSlide.value = e.detail.current
}

function nextSlide() {
  if (currentSlide.value < slides.length - 1) {
    currentSlide.value++
  }
}

function finish() {
  uni.setStorageSync('guideShown', 'true')
  uni.reLaunch({ url: '/pages/home/index' })
}
</script>

<style lang="scss" scoped>
.guide-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  padding-bottom: env(safe-area-inset-bottom);
}

.guide-swiper {
  flex: 1;
  width: 100%;
}

.slide-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 80rpx 60rpx;
}

.slide-visual {
  width: 320rpx;
  height: 320rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 60rpx;
}

.slide-emoji {
  font-size: 120rpx;
}

.slide-title {
  font-size: 44rpx;
  font-weight: 700;
  color: #fff;
  margin-bottom: 24rpx;
}

.slide-desc {
  font-size: 30rpx;
  color: rgba(255, 255, 255, 0.85);
  text-align: center;
  line-height: 1.6;
}

.indicators {
  display: flex;
  justify-content: center;
  gap: 16rpx;
  padding: 32rpx 0;
}

.indicator-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 8rpx;
  background: rgba(255, 255, 255, 0.4);
  transition: all 0.3s;

  &.active {
    width: 40rpx;
    background: #fff;
  }
}

.bottom-actions {
  padding: 32rpx 48rpx 64rpx;
}

.action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;

  &.center {
    justify-content: center;
  }
}

.skip-btn {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.7);
  padding: 16rpx 32rpx;
}

.next-btn {
  padding: 24rpx 56rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 40rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.5);
}

.next-btn-text {
  font-size: 28rpx;
  color: #fff;
  font-weight: 500;
}

.start-btn {
  padding: 28rpx 80rpx;
  background: #fff;
  border-radius: 44rpx;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.15);
}

.start-btn-text {
  font-size: 32rpx;
  color: #667eea;
  font-weight: 600;
}
</style>
