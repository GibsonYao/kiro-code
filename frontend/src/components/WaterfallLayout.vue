<template>
  <!-- 瀑布流布局组件 (Task 20.1) -->
  <view class="waterfall" :style="{ gap: `${gap}rpx` }">
    <view
      v-for="(column, colIndex) in columns"
      :key="colIndex"
      class="waterfall__column"
      :style="{ gap: `${gap}rpx` }"
    >
      <view
        v-for="(item, itemIndex) in column"
        :key="item.id || itemIndex"
        class="waterfall__item"
        @tap="$emit('item-tap', item)"
      >
        <slot :item="item" :index="getOriginalIndex(colIndex, itemIndex)" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface WaterfallItem {
  id?: string
  [key: string]: unknown
}

const props = withDefaults(
  defineProps<{
    /** 数据列表 */
    items: WaterfallItem[]
    /** 列数 */
    columnCount?: number
    /** 间距（rpx） */
    gap?: number
  }>(),
  {
    columnCount: 2,
    gap: 20,
  }
)

defineEmits<{
  'item-tap': [item: WaterfallItem]
}>()

/** 将items分配到各列（简单轮询分配） */
const columns = computed(() => {
  const cols: WaterfallItem[][] = Array.from({ length: props.columnCount }, () => [])

  props.items.forEach((item, index) => {
    const colIndex = index % props.columnCount
    cols[colIndex].push(item)
  })

  return cols
})

/** 获取原始索引 */
function getOriginalIndex(colIndex: number, itemIndex: number): number {
  return itemIndex * props.columnCount + colIndex
}
</script>

<style lang="scss" scoped>
.waterfall {
  display: flex;
  width: 100%;
  padding: 0 20rpx;
  box-sizing: border-box;
}

.waterfall__column {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.waterfall__item {
  break-inside: avoid;
}
</style>
