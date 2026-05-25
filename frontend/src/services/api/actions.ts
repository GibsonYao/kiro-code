// ============================================
// 行动模块 API
// ============================================

import { get, post, put, del } from '../request'
import type {
  ActionItem,
  ActionListResponse,
  ActionCreateRequest,
  ActionUpdateRequest,
  ActionTimeLogRequest,
} from '../types'

export const actionApi = {
  /** 获取行动列表（分页） */
  getActions(params: { page?: number; page_size?: number; action_type?: string; status?: string } = {}): Promise<ActionListResponse> {
    return get<ActionListResponse>('/actions', params)
  },

  /** 获取单个行动详情 */
  getAction(id: string): Promise<ActionItem> {
    return get<ActionItem>(`/actions/${id}`)
  },

  /** 创建行动 */
  createAction(data: ActionCreateRequest): Promise<ActionItem> {
    return post<ActionItem>('/actions', data as unknown as Record<string, unknown>)
  },

  /** 更新行动 */
  updateAction(id: string, data: ActionUpdateRequest): Promise<ActionItem> {
    return put<ActionItem>(`/actions/${id}`, data as unknown as Record<string, unknown>)
  },

  /** 删除行动 */
  deleteAction(id: string): Promise<void> {
    return del<void>(`/actions/${id}`)
  },

  /** 标记行动完成 */
  completeAction(id: string): Promise<ActionItem> {
    return post<ActionItem>(`/actions/${id}/complete`)
  },

  /** 记录时间 */
  updateTimeLog(id: string, data: ActionTimeLogRequest): Promise<ActionItem> {
    return put<ActionItem>(`/actions/${id}/time-log`, data as unknown as Record<string, unknown>)
  },
}
