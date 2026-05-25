import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { goalApi } from '@/services/api/goals'
import type { GoalItem, GoalStatus, GoalChainResponse } from '@/services/types'

export const useGoalStore = defineStore('goal', () => {
  // --- State ---
  const goals = ref<GoalItem[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)
  const loading = ref(false)
  const creating = ref(false)
  const currentGoalChain = ref<GoalChainResponse | null>(null)
  const chainLoading = ref(false)

  // --- Getters ---
  const activeGoals = computed(() => goals.value.filter(g => g.status === 'active'))
  const isEmpty = computed(() => goals.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 获取目标列表（首次加载或刷新） */
  async function fetchGoals(status?: GoalStatus): Promise<void> {
    loading.value = true
    try {
      currentPage.value = 1
      const res = await goalApi.getGoals({
        page: 1,
        page_size: pageSize.value,
        status,
      })
      goals.value = res.items
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
      const res = await goalApi.getGoals({
        page: nextPage,
        page_size: pageSize.value,
      })
      goals.value = [...goals.value, ...res.items]
      currentPage.value = nextPage
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 创建目标 */
  async function createGoal(data: { title: string; description?: string; wish_id?: string }): Promise<GoalItem> {
    creating.value = true
    try {
      const goal = await goalApi.createGoal(data)
      // 插入到列表头部
      goals.value.unshift(goal)
      total.value += 1
      return goal
    } finally {
      creating.value = false
    }
  }

  /** 更新目标 */
  async function updateGoal(id: string, data: { title?: string; description?: string; status?: GoalStatus; progress?: number }): Promise<GoalItem> {
    const goal = await goalApi.updateGoal(id, data)
    // 更新列表中的对应项
    const index = goals.value.findIndex(g => g.id === id)
    if (index !== -1) {
      goals.value[index] = goal
    }
    return goal
  }

  /** 删除目标 */
  async function deleteGoal(id: string): Promise<void> {
    await goalApi.deleteGoal(id)
    goals.value = goals.value.filter(g => g.id !== id)
    total.value -= 1
  }

  /** 获取目标完整链路 */
  async function fetchGoalChain(id: string): Promise<GoalChainResponse> {
    chainLoading.value = true
    try {
      const chain = await goalApi.getGoalChain(id)
      currentGoalChain.value = chain
      return chain
    } finally {
      chainLoading.value = false
    }
  }

  /** 重置状态 */
  function reset(): void {
    goals.value = []
    total.value = 0
    currentPage.value = 1
    hasMore.value = false
    loading.value = false
    creating.value = false
    currentGoalChain.value = null
    chainLoading.value = false
  }

  return {
    // State
    goals,
    total,
    currentPage,
    pageSize,
    hasMore,
    loading,
    creating,
    currentGoalChain,
    chainLoading,
    // Getters
    activeGoals,
    isEmpty,
    // Actions
    fetchGoals,
    loadMore,
    createGoal,
    updateGoal,
    deleteGoal,
    fetchGoalChain,
    reset,
  }
})
