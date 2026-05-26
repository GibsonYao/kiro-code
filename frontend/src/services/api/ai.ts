// ============================================
// AI生成相关API (Task 15.3)
// ============================================

import { get, post } from '../request'

/** AI生成状态响应 */
export interface GenerationStatusResponse {
  task_id: string
  status: 'pending' | 'started' | 'completed' | 'failed'
  result?: unknown
}

/** 重新生成请求 */
export interface RegenerateRequest {
  entity_type: string
  entity_id: string
  style?: string
}

/** 图片风格 */
export interface ImageStyle {
  id: string
  name: string
  description: string
  preview_url?: string
}

export const aiApi = {
  /** 查询AI生成任务状态 */
  getGenerationStatus(taskId: string) {
    return get<GenerationStatusResponse>(`/ai/generation/${taskId}/status`)
  },

  /** 重新生成配图 */
  regenerateImage(data: RegenerateRequest) {
    return post<{ task_id: string }>('/ai/regenerate-image', data as unknown as Record<string, unknown>)
  },

  /** 重新生成文案 */
  regenerateText(data: RegenerateRequest) {
    return post<{ task_id: string }>('/ai/regenerate-text', data as unknown as Record<string, unknown>)
  },

  /** 获取可用图片风格列表 */
  getStyles() {
    return get<{ styles: ImageStyle[] }>('/ai/styles')
  },
}
