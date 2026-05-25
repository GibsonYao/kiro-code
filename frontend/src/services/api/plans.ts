// ============================================
// 计划模块 API
// ============================================

import { get, post, put, del } from '../request'
import type {
  PlanItem,
  PlanListResponse,
  PlanCreateRequest,
  PlanUpdateRequest,
  PlanStepItem,
  PlanStepCreateRequest,
  PlanStepUpdateRequest,
} from '../types'

export const planApi = {
  /** 获取计划列表（分页） */
  getPlans(params: { page?: number; page_size?: number; status?: string } = {}): Promise<PlanListResponse> {
    return get<PlanListResponse>('/plans', params)
  },

  /** 获取单个计划详情 */
  getPlan(id: string): Promise<PlanItem> {
    return get<PlanItem>(`/plans/${id}`)
  },

  /** 创建计划 */
  createPlan(data: PlanCreateRequest): Promise<PlanItem> {
    return post<PlanItem>('/plans', data as unknown as Record<string, unknown>)
  },

  /** 更新计划 */
  updatePlan(id: string, data: PlanUpdateRequest): Promise<PlanItem> {
    return put<PlanItem>(`/plans/${id}`, data as unknown as Record<string, unknown>)
  },

  /** 删除计划 */
  deletePlan(id: string): Promise<void> {
    return del<void>(`/plans/${id}`)
  },

  // ─── 步骤管理 ─────────────────────────────────────────────────────────────

  /** 创建步骤 */
  createStep(planId: string, data: PlanStepCreateRequest): Promise<PlanStepItem> {
    return post<PlanStepItem>(`/plans/${planId}/steps`, data as unknown as Record<string, unknown>)
  },

  /** 更新步骤 */
  updateStep(planId: string, stepId: string, data: PlanStepUpdateRequest): Promise<PlanStepItem> {
    return put<PlanStepItem>(`/plans/${planId}/steps/${stepId}`, data as unknown as Record<string, unknown>)
  },

  /** 删除步骤 */
  deleteStep(planId: string, stepId: string): Promise<void> {
    return del<void>(`/plans/${planId}/steps/${stepId}`)
  },
}
