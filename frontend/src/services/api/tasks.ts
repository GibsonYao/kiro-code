// ============================================
// 任务模块 API
// ============================================

import { get, post, put, del } from '../request'
import type {
  TaskItem,
  TaskListResponse,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskSubmitRequest,
} from '../types'

export const taskApi = {
  /** 获取任务列表（分页） */
  getTasks(params: { page?: number; page_size?: number; status?: string; assignee_id?: string } = {}): Promise<TaskListResponse> {
    return get<TaskListResponse>('/tasks', params)
  },

  /** 获取可认领悬赏任务列表 */
  getBountyTasks(params: { page?: number; page_size?: number } = {}): Promise<TaskListResponse> {
    return get<TaskListResponse>('/tasks/bounty', params)
  },

  /** 获取单个任务详情 */
  getTask(id: string): Promise<TaskItem> {
    return get<TaskItem>(`/tasks/${id}`)
  },

  /** 创建任务 */
  createTask(data: TaskCreateRequest): Promise<TaskItem> {
    return post<TaskItem>('/tasks', data as unknown as Record<string, unknown>)
  },

  /** 更新任务 */
  updateTask(id: string, data: TaskUpdateRequest): Promise<TaskItem> {
    return put<TaskItem>(`/tasks/${id}`, data as unknown as Record<string, unknown>)
  },

  /** 删除任务 */
  deleteTask(id: string): Promise<void> {
    return del<void>(`/tasks/${id}`)
  },

  /** 认领悬赏任务 */
  claimTask(id: string): Promise<TaskItem> {
    return post<TaskItem>(`/tasks/${id}/claim`)
  },

  /** 提交任务完成 */
  submitTask(id: string, data: TaskSubmitRequest): Promise<TaskItem> {
    return post<TaskItem>(`/tasks/${id}/submit`, data as unknown as Record<string, unknown>)
  },
}
