<template>
  <!-- 图片风格选择组件 (Task 15.3) -->
  <view class="style-selector">
    <view class="style-selector__label">
      <text class="style-selector__label-text">选择图片风格</text>
    </view>
    <view class="style-selector__list">
      <view
        v-for="style in styleList"
        :key="style.id"
        class="style-selector__chip"
        :class="{ 'style-selector__chip--active': modelValue === style.id }"
        @tap="selectStyle(style.id)"
      >
        <text class="style-selector__chip-text">{{ style.name }}</text>
      </view>
    </view>
    <text v-if="selectedDescription" class="style-selector__description">
      {{ selectedDescription }}
    </text>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAIStatusStore, type ImageStyle } from '@/stores/aiStatus'

const props = defineProps<{
  /** 当前选中的风格ID */
  modelValue?: string
  /** 自定义风格列表（可选，不传则从store获取） */
  styles?: ImageStyle[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const aiStatusStore = useAIStatusStore()

/** 实际使用的风格列表 */
const styleList = computed(() => {
  if (props.styles && props.styles.length > 0) {
    return props.styles
  }
  return aiStatusStore.styles.length > 0
    ? aiStatusStore.styles
    : []
})

/** 选中风格的描述 */
const selectedDescription = computed(() => {
  if (!props.modelValue) return ''
  const found = styleList.value.find(s => s.id === props.modelValue)
  return found?.description || ''
})

/** 选择风格 */
function selectStyle(styleId: string) {
  emit('update:modelValue', styleId)
}

/** 组件挂载时加载风格列表 */
onMounted(() => {
  if (!props.styles || props.styles.length === 0) {
    aiStatusStore.fetchStyles()
  }
})
</script>

<style lang="scss" scoped>
.style-selector {
  padding: 24rpx 0;
}

.style-selector__label {
  margin-bottom: 16rpx;
}

.style-selector__label-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #1a1a2e;
}

.style-selector__list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.style-selector__chip {
  padding: 14rpx 28rpx;
  border-radius: 32rpx;
  background: #f5f6fa;
  border: 2rpx solid #e8eaed;
  transition: all 0.2s ease;

  &:active {
    transform: scale(0.95);
  }

  &--active {
    background: rgba(74, 144, 217, 0.1);
    border-color: #4a90d9;
  }
}

.style-selector__chip-text {
  font-size: 26rpx;
  color: #4a5568;

  .style-selector__chip--active & {
    color: #4a90d9;
    font-weight: 500;
  }
}

.style-selector__description {
  margin-top: 16rpx;
  font-size: 24rpx;
  color: #718096;
  line-height: 1.4;
}
</style>
