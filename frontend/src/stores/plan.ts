import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { planApi } from '@/services/api/plans'
import type { PlanItem, PlanStatus, PlanStepItem, PlanStepCreateRequest, PlanStepUpdateRequest } from '@/services/types'

export const usePlanStore = defineStore('plan', () => {
  // --- State ---
  const plans = ref<PlanItem[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)
  const loading = ref(false)
  const creating = ref(false)
  const currentPlan = ref<PlanItem | null>(null)

  // --- Getters ---
  const activePlans = computed(() => plans.value.filter(p => p.status === 'active'))
  const isEmpty = computed(() => plans.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 获取计划列表（首次加载或刷新） */
  async function fetchPlans(status?: PlanStatus): Promise<void> {
    loading.value = true
    try {
      currentPage.value = 1
      const res = await planApi.getPlans({
        page: 1,
        page_size: pageSize.value,
        status,
      })
      plans.value = res.items
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 加载更多（分页） */
  async function loadMore(): Promise<void> {
    if (!hasMore.value || loading.value) return

    loading.value = true
    try {
      const nextPage = currentPage.value + 1
      const res = await planApi.getPlans({
        page: nextPage,
        page_size: pageSize.value,
      })
      plans.value = [...plans.value, ...res.items]
      currentPage.value = nextPage
      total.value = res.total
      hasMore.value = res.has_more
    } finally {
      loading.value = false
    }
  }

  /** 获取计划详情 */
  async function fetchPlan(id: string): Promise<PlanItem> {
    const plan = await planApi.getPlan(id)
    currentPlan.value = plan
    return plan
  }

  /** 创建计划 */
  async function createPlan(data: {
    title: string
    goal_id?: string
    start_date?: string
    end_date?: string
    owner_id: string
  }): Promise<PlanItem> {
    creating.value = true
    try {
      const plan = await planApi.createPlan(data)
      plans.value.unshift(plan)
      total.value += 1
      return plan
    } finally {
      creating.value = false
    }
  }

  /** 更新计划 */
  async function updatePlan(id: string, data: {
    title?: string
    start_date?: string
    end_date?: string
    owner_id?: string
    status?: PlanStatus
  }): Promise<PlanItem> {
    const plan = await planApi.updatePlan(id, data)
    const index = plans.value.findIndex(p => p.id === id)
    if (index !== -1) {
      plans.value[index] = plan
    }
    if (currentPlan.value?.id === id) {
      currentPlan.value = plan
    }
    return plan
  }

  /** 删除计划 */
  async function deletePlan(id: string): Promise<void> {
    await planApi.deletePlan(id)
    plans.value = plans.value.filter(p => p.id !== id)
    total.value -= 1
    if (currentPlan.value?.id === id) {
      currentPlan.value = null
    }
  }

  // ─── 步骤管理 ─────────────────────────────────────────────────────────────

  /** 添加步骤 */
  async function addStep(planId: string, data: PlanStepCreateRequest): Promise<PlanStepItem> {
    const step = await planApi.createStep(planId, data)
    // Update local state
    if (currentPlan.value?.id === planId) {
      currentPlan.value.steps.push(step)
      currentPlan.value.steps.sort((a, b) => a.sort_order - b.sort_order)
    }
    const planInList = plans.value.find(p => p.id === planId)
    if (planInList) {
      planInList.steps.push(step)
      planInList.steps.sort((a, b) => a.sort_order - b.sort_order)
    }
    return step
  }

  /** 更新步骤 */
  async function updateStep(planId: string, stepId: string, data: PlanStepUpdateRequest): Promise<PlanStepItem> {
    const step = await planApi.updateStep(planId, stepId, data)
    // Update local state
    const updateInPlan = (plan: PlanItem) => {
      const idx = plan.steps.findIndex(s => s.id === stepId)
      if (idx !== -1) {
        plan.steps[idx] = step
      }
    }
    if (currentPlan.value?.id === planId) {
      updateInPlan(currentPlan.value)
    }
    const planInList = plans.value.find(p => p.id === planId)
    if (planInList) {
      updateInPlan(planInList)
    }
    return step
  }

  /** 删除步骤 */
  async function deleteStep(planId: string, stepId: string): Promise<void> {
    await planApi.deleteStep(planId, stepId)
    // Update local state
    const removeFromPlan = (plan: PlanItem) => {
      plan.steps = plan.steps.filter(s => s.id !== stepId)
    }
    if (currentPlan.value?.id === planId) {
      removeFromPlan(currentPlan.value)
    }
    const planInList = plans.value.find(p => p.id === planId)
    if (planInList) {
      removeFromPlan(planInList)
    }
  }

  /** 重置状态 */
  function reset(): void {
    plans.value = []
    total.value = 0
    currentPage.value = 1
    hasMore.value = false
    loading.value = false
    creating.value = false
    currentPlan.value = null
  }

  return {
    // State
    plans,
    total,
    currentPage,
    pageSize,
    hasMore,
    loading,
    creating,
    currentPlan,
    // Getters
    activePlans,
    isEmpty,
    // Actions
    fetchPlans,
    loadMore,
    fetchPlan,
    createPlan,
    updatePlan,
    deletePlan,
    addStep,
    updateStep,
    deleteStep,
    reset,
  }
})
