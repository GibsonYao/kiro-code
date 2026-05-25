import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { actionApi } from '@/services/api/actions'
import type { ActionItem, ActionType, ActionStatus } from '@/services/types'

export const useActionStore = defineStore('action', () => {
  // --- State ---
  const actions = ref<ActionItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)
  const loading = ref(false)
  const creating = ref(false)

  // --- Getters ---
  const todoActions = computed(() =>
    actions.value.filter(a => a.action_type === 'todo')
  )
  const scheduleActions = computed(() =>
    actions.value.filter(a => a.action_type === 'schedule')
  )
  const isEmpty = computed(() => actions.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 获取行动列表（首次加载或刷新） */
  async function fetchActions(actionType?: ActionType, status?: ActionStatus): Promise<void> {
    loading.value = true
    try {
      page.value = 1
      const res = await actionApi.getActions({
        page: 1,
        page_size: pageSize.value,
        action_type: actionType,
        status,
      })
      actions.value = res.items
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 加载更多行动 */
  async function loadMore(actionType?: ActionType): Promise<void> {
    if (!hasMore.value || loading.value) return

    loading.value = true
    try {
      const nextPage = page.value + 1
      const res = await actionApi.getActions({
        page: nextPage,
        page_size: pageSize.value,
        action_type: actionType,
      })
      actions.value = [...actions.value, ...res.items]
      page.value = nextPage
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 创建行动 */
  async function createAction(data: Parameters<typeof actionApi.createAction>[0]): Promise<ActionItem> {
    creating.value = true
    try {
      const action = await actionApi.createAction(data)
      actions.value.unshift(action)
      total.value += 1
      return action
    } finally {
      creating.value = false
    }
  }

  /** 标记行动完成 */
  async function completeAction(id: string): Promise<ActionItem> {
    const action = await actionApi.completeAction(id)
    const index = actions.value.findIndex(a => a.id === id)
    if (index !== -1) {
      actions.value[index] = action
    }
    return action
  }

  /** 记录时间 */
  async function updateTimeLog(id: string, minutes: number): Promise<ActionItem> {
    const action = await actionApi.updateTimeLog(id, { time_spent_minutes: minutes })
    const index = actions.value.findIndex(a => a.id === id)
    if (index !== -1) {
      actions.value[index] = action
    }
    return action
  }

  /** 删除行动 */
  async function deleteAction(id: string): Promise<void> {
    await actionApi.deleteAction(id)
    actions.value = actions.value.filter(a => a.id !== id)
    total.value -= 1
  }

  /** 重置状态 */
  function reset(): void {
    actions.value = []
    total.value = 0
    page.value = 1
    hasMore.value = false
    loading.value = false
    creating.value = false
  }

  return {
    // State
    actions,
    total,
    hasMore,
    loading,
    creating,
    // Getters
    todoActions,
    scheduleActions,
    isEmpty,
    // Actions
    fetchActions,
    loadMore,
    createAction,
    completeAction,
    updateTimeLog,
    deleteAction,
    reset,
  }
})
