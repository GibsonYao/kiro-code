// ============================================
// 目标模块 API
// ============================================

import { get, post, put, del } from '../request'
import type {
  GoalItem,
  GoalListResponse,
  GoalCreateRequest,
  GoalUpdateRequest,
  GoalChainResponse,
} from '../types'

export const goalApi = {
  /** 获取目标列表（分页） */
  getGoals(params: { page?: number; page_size?: number; status?: string } = {}): Promise<GoalListResponse> {
    return get<GoalListResponse>('/goals', params)
  },

  /** 获取单个目标详情 */
  getGoal(id: string): Promise<GoalItem> {
    return get<GoalItem>(`/goals/${id}`)
  },

  /** 创建目标 */
  createGoal(data: GoalCreateRequest): Promise<GoalItem> {
    return post<GoalItem>('/goals', data as unknown as Record<string, unknown>)
  },

  /** 更新目标 */
  updateGoal(id: string, data: GoalUpdateRequest): Promise<GoalItem> {
    return put<GoalItem>(`/goals/${id}`, data as unknown as Record<string, unknown>)
  },

  /** 删除目标 */
  deleteGoal(id: string): Promise<void> {
    return del<void>(`/goals/${id}`)
  },

  /** 获取目标完整链路 */
  getGoalChain(id: string): Promise<GoalChainResponse> {
    return get<GoalChainResponse>(`/goals/${id}/chain`)
  },
}
