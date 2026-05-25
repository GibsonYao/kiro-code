import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { reviewApi } from '@/services/api/reviews'
import type { ReviewItem } from '@/services/types'

export const useReviewStore = defineStore('review', () => {
  // --- State ---
  const pendingReviews = ref<ReviewItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)
  const loading = ref(false)

  // --- Getters ---
  const isEmpty = computed(() => pendingReviews.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 获取待审核列表（首次加载或刷新） */
  async function fetchPendingReviews(): Promise<void> {
    loading.value = true
    try {
      page.value = 1
      const res = await reviewApi.getPendingReviews({
        page: 1,
        page_size: pageSize.value,
      })
      pendingReviews.value = res.items
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 加载更多 */
  async function loadMore(): Promise<void> {
    if (!hasMore.value || loading.value) return

    loading.value = true
    try {
      const nextPage = page.value + 1
      const res = await reviewApi.getPendingReviews({
        page: nextPage,
        page_size: pageSize.value,
      })
      pendingReviews.value = [...pendingReviews.value, ...res.items]
      page.value = nextPage
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 通过审核 */
  async function approveReview(id: string, comment?: string): Promise<void> {
    await reviewApi.approveReview(id, comment ? { comment } : undefined)
    pendingReviews.value = pendingReviews.value.filter(r => r.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  /** 驳回审核 */
  async function rejectReview(id: string, comment?: string): Promise<void> {
    await reviewApi.rejectReview(id, comment ? { comment } : undefined)
    pendingReviews.value = pendingReviews.value.filter(r => r.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  /** 重置状态 */
  function reset(): void {
    pendingReviews.value = []
    total.value = 0
    page.value = 1
    hasMore.value = false
    loading.value = false
  }

  return {
    // State
    pendingReviews,
    total,
    hasMore,
    loading,
    // Getters
    isEmpty,
    // Actions
    fetchPendingReviews,
    loadMore,
    approveReview,
    rejectReview,
    reset,
  }
})
