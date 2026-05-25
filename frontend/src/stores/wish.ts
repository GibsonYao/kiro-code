import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { wishApi } from '@/services/api/wishes'
import type { WishItem, WishStatus } from '@/services/types'

export const useWishStore = defineStore('wish', () => {
  // --- State ---
  const wishes = ref<WishItem[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)
  const loading = ref(false)
  const creating = ref(false)

  // --- Getters ---
  const activeWishes = computed(() => wishes.value.filter(w => w.status === 'active'))
  const isEmpty = computed(() => wishes.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 获取愿望列表（首次加载或刷新） */
  async function fetchWishes(status?: WishStatus): Promise<void> {
    loading.value = true
    try {
      currentPage.value = 1
      const res = await wishApi.getWishes({
        page: 1,
        page_size: pageSize.value,
        status,
      })
      wishes.value = res.items
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 加载更多（瀑布流分页） */
  async function loadMore(): Promise<void> {
    if (!hasMore.value || loading.value) return

    loading.value = true
    try {
      const nextPage = currentPage.value + 1
      const res = await wishApi.getWishes({
        page: nextPage,
        page_size: pageSize.value,
      })
      wishes.value = [...wishes.value, ...res.items]
      currentPage.value = nextPage
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 创建愿望 */
  async function createWish(title: string): Promise<WishItem> {
    creating.value = true
    try {
      const wish = await wishApi.createWish({ title })
      // 插入到列表头部
      wishes.value.unshift(wish)
      total.value += 1
      return wish
    } finally {
      creating.value = false
    }
  }

  /** 更新愿望 */
  async function updateWish(id: string, data: { title?: string; status?: WishStatus }): Promise<WishItem> {
    const wish = await wishApi.updateWish(id, data)
    // 更新列表中的对应项
    const index = wishes.value.findIndex(w => w.id === id)
    if (index !== -1) {
      wishes.value[index] = wish
    }
    return wish
  }

  /** 删除愿望 */
  async function deleteWish(id: string): Promise<void> {
    await wishApi.deleteWish(id)
    wishes.value = wishes.value.filter(w => w.id !== id)
    total.value -= 1
  }

  /** 重新生成愿景 */
  async function regenerateVision(id: string): Promise<WishItem> {
    const wish = await wishApi.regenerateVision(id)
    const index = wishes.value.findIndex(w => w.id === id)
    if (index !== -1) {
      wishes.value[index] = wish
    }
    return wish
  }

  /** 重置状态 */
  function reset(): void {
    wishes.value = []
    total.value = 0
    currentPage.value = 1
    hasMore.value = false
    loading.value = false
    creating.value = false
  }

  return {
    // State
    wishes,
    total,
    currentPage,
    pageSize,
    hasMore,
    loading,
    creating,
    // Getters
    activeWishes,
    isEmpty,
    // Actions
    fetchWishes,
    loadMore,
    createWish,
    updateWish,
    deleteWish,
    regenerateVision,
    reset,
  }
})
