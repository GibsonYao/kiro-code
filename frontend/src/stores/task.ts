import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { taskApi } from '@/services/api/tasks'
import type { TaskItem, TaskStatus, TaskSubmitRequest } from '@/services/types'

export const useTaskStore = defineStore('task', () => {
  // --- State ---
  const myTasks = ref<TaskItem[]>([])
  const bountyTasks = ref<TaskItem[]>([])
  const myTotal = ref(0)
  const bountyTotal = ref(0)
  const myPage = ref(1)
  const bountyPage = ref(1)
  const pageSize = ref(20)
  const myHasMore = ref(false)
  const bountyHasMore = ref(false)
  const loading = ref(false)
  const creating = ref(false)

  // --- Getters ---
  const pendingReviews = computed(() =>
    myTasks.value.filter(t => t.status === 'submitted')
  )
  const isEmpty = computed(() => myTasks.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 获取我的任务列表（首次加载或刷新） */
  async function fetchMyTasks(status?: TaskStatus, assigneeId?: string): Promise<void> {
    loading.value = true
    try {
      myPage.value = 1
      const res = await taskApi.getTasks({
        page: 1,
        page_size: pageSize.value,
        status,
        assignee_id: assigneeId,
      })
      myTasks.value = res.items
      myTotal.value = res.total
      myHasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 加载更多我的任务 */
  async function loadMoreMyTasks(): Promise<void> {
    if (!myHasMore.value || loading.value) return

    loading.value = true
    try {
      const nextPage = myPage.value + 1
      const res = await taskApi.getTasks({
        page: nextPage,
        page_size: pageSize.value,
      })
      myTasks.value = [...myTasks.value, ...res.items]
      myPage.value = nextPage
      myTotal.value = res.total
      myHasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 获取悬赏任务列表 */
  async function fetchBountyTasks(): Promise<void> {
    loading.value = true
    try {
      bountyPage.value = 1
      const res = await taskApi.getBountyTasks({
        page: 1,
        page_size: pageSize.value,
      })
      bountyTasks.value = res.items
      bountyTotal.value = res.total
      bountyHasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 加载更多悬赏任务 */
  async function loadMoreBountyTasks(): Promise<void> {
    if (!bountyHasMore.value || loading.value) return

    loading.value = true
    try {
      const nextPage = bountyPage.value + 1
      const res = await taskApi.getBountyTasks({
        page: nextPage,
        page_size: pageSize.value,
      })
      bountyTasks.value = [...bountyTasks.value, ...res.items]
      bountyPage.value = nextPage
      bountyTotal.value = res.total
      bountyHasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 认领悬赏任务 */
  async function claimTask(taskId: string): Promise<TaskItem> {
    const task = await taskApi.claimTask(taskId)
    // Remove from bounty list
    bountyTasks.value = bountyTasks.value.filter(t => t.id !== taskId)
    bountyTotal.value -= 1
    // Add to my tasks
    myTasks.value.unshift(task)
    myTotal.value += 1
    return task
  }

  /** 提交任务完成 */
  async function submitTask(taskId: string, data: TaskSubmitRequest): Promise<TaskItem> {
    const task = await taskApi.submitTask(taskId, data)
    // Update in my tasks list
    const index = myTasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      myTasks.value[index] = task
    }
    return task
  }

  /** 创建任务 */
  async function createTask(data: Parameters<typeof taskApi.createTask>[0]): Promise<TaskItem> {
    creating.value = true
    try {
      const task = await taskApi.createTask(data)
      myTasks.value.unshift(task)
      myTotal.value += 1
      return task
    } finally {
      creating.value = false
    }
  }

  /** 删除任务 */
  async function deleteTask(id: string): Promise<void> {
    await taskApi.deleteTask(id)
    myTasks.value = myTasks.value.filter(t => t.id !== id)
    myTotal.value -= 1
  }

  /** 重置状态 */
  function reset(): void {
    myTasks.value = []
    bountyTasks.value = []
    myTotal.value = 0
    bountyTotal.value = 0
    myPage.value = 1
    bountyPage.value = 1
    myHasMore.value = false
    bountyHasMore.value = false
    loading.value = false
    creating.value = false
  }

  return {
    // State
    myTasks,
    bountyTasks,
    myTotal,
    bountyTotal,
    myHasMore,
    bountyHasMore,
    loading,
    creating,
    // Getters
    pendingReviews,
    isEmpty,
    // Actions
    fetchMyTasks,
    loadMoreMyTasks,
    fetchBountyTasks,
    loadMoreBountyTasks,
    claimTask,
    submitTask,
    createTask,
    deleteTask,
    reset,
  }
})
