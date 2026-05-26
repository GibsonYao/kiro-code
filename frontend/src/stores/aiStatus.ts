// ============================================
// AI生成状态管理 Store (Task 15.1 + 15.4 + 15.5 + 15.6)
// 管理AI内容生成的轮询状态、完成回调、重新生成、风格列表
// ============================================

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { get, post } from '@/services/request'

/** AI生成任务状态 */
export type GenerationStatus = 'pending' | 'started' | 'completed' | 'failed'

/** 生成任务信息 */
export interface GenerationTask {
  taskId: string
  entityType: string
  entityId: string
  status: GenerationStatus
  result?: unknown
  /** 轮询定时器ID */
  timerId?: number
  /** 生成完成回调 */
  onComplete?: (result: unknown) => void
}

/** 生成状态API响应 */
interface GenerationStatusResponse {
  task_id: string
  status: GenerationStatus
  result?: unknown
}

/** 重新生成请求参数 */
interface RegenerateRequest {
  entity_type: string
  entity_id: string
  style?: string
}

/** 重新生成响应 */
interface RegenerateResponse {
  task_id: string
}

/** 图片风格 */
export interface ImageStyle {
  id: string
  name: string
  description: string
  preview_url?: string | null
}

/** 风格列表响应 */
interface StylesResponse {
  styles: ImageStyle[]
}

/** 默认风格列表（API不可用时的降级方案） */
const DEFAULT_STYLES: ImageStyle[] = [
  { id: 'realistic', name: '写实风格', description: '真实感强的照片级图片' },
  { id: 'illustration', name: '插画风格', description: '温暖手绘插画风格' },
  { id: 'flat', name: '扁平化', description: '现代简洁的扁平设计风格' },
  { id: 'watercolor', name: '水彩风格', description: '柔和梦幻的水彩画风格' },
  { id: 'anime', name: '动漫风格', description: '日系动漫插画风格' },
]

export const useAIStatusStore = defineStore('aiStatus', () => {
  // ─── State ────────────────────────────────────────────────────────────────
  const pendingGenerations = ref<Map<string, GenerationTask>>(new Map())
  const styles = ref<ImageStyle[]>([])
  const stylesLoading = ref(false)

  // ─── 轮询间隔（3秒） ─────────────────────────────────────────────────────
  const POLL_INTERVAL = 3000

  // ─── Actions ──────────────────────────────────────────────────────────────

  /**
   * 开始追踪一个AI生成任务
   * @param taskId Celery任务ID
   * @param entityType 实体类型 (wish/goal/plan/task/action)
   * @param entityId 实体UUID
   * @param onComplete 生成完成时的回调
   */
  function trackGeneration(
    taskId: string,
    entityType: string,
    entityId: string,
    onComplete?: (result: unknown) => void
  ) {
    const task: GenerationTask = {
      taskId,
      entityType,
      entityId,
      status: 'pending',
      onComplete,
    }

    pendingGenerations.value.set(taskId, task)

    // 开始轮询
    startPolling(taskId)
  }

  /**
   * 开始轮询生成状态
   */
  function startPolling(taskId: string) {
    const poll = async () => {
      const task = pendingGenerations.value.get(taskId)
      if (!task) return

      try {
        const response = await checkStatus(taskId)

        task.status = response.status
        task.result = response.result

        if (response.status === 'completed' || response.status === 'failed') {
          // 生成完成或失败，停止轮询
          stopPolling(taskId)

          if (response.status === 'completed' && task.onComplete) {
            task.onComplete(response.result)
          }

          // 3秒后从Map中移除已完成的任务
          setTimeout(() => {
            pendingGenerations.value.delete(taskId)
          }, 3000)
        } else {
          // 继续轮询
          task.timerId = setTimeout(poll, POLL_INTERVAL) as unknown as number
        }
      } catch {
        // 网络错误，延长轮询间隔后重试
        task.timerId = setTimeout(poll, POLL_INTERVAL * 2) as unknown as number
      }
    }

    // 首次延迟1秒后开始轮询
    const timerId = setTimeout(poll, 1000) as unknown as number
    const task = pendingGenerations.value.get(taskId)
    if (task) {
      task.timerId = timerId
    }
  }

  /**
   * 停止轮询
   */
  function stopPolling(taskId: string) {
    const task = pendingGenerations.value.get(taskId)
    if (task?.timerId) {
      clearTimeout(task.timerId)
      task.timerId = undefined
    }
  }

  /**
   * 查询单个任务的生成状态（对接 GET /api/v1/ai/generation/{task_id}/status）
   */
  async function checkStatus(taskId: string): Promise<GenerationStatusResponse> {
    return await get<GenerationStatusResponse>(`/ai/generation/${taskId}/status`)
  }

  /**
   * 重新生成配图（调用 POST /api/v1/ai/regenerate-image）
   * @param entityType 实体类型
   * @param entityId 实体ID
   * @param style 图片风格（可选）
   * @param onComplete 生成完成回调
   * @returns 新的任务ID
   */
  async function regenerateImage(
    entityType: string,
    entityId: string,
    style?: string,
    onComplete?: (result: unknown) => void
  ): Promise<string> {
    const body: RegenerateRequest = {
      entity_type: entityType,
      entity_id: entityId,
    }
    if (style) {
      body.style = style
    }

    const response = await post<RegenerateResponse>('/ai/regenerate-image', body)

    // 自动开始追踪新任务
    trackGeneration(response.task_id, entityType, entityId, onComplete)

    return response.task_id
  }

  /**
   * 重新生成文案（调用 POST /api/v1/ai/regenerate-text）
   * @param entityType 实体类型
   * @param entityId 实体ID
   * @param onComplete 生成完成回调
   * @returns 新的任务ID
   */
  async function regenerateText(
    entityType: string,
    entityId: string,
    onComplete?: (result: unknown) => void
  ): Promise<string> {
    const body: RegenerateRequest = {
      entity_type: entityType,
      entity_id: entityId,
    }

    const response = await post<RegenerateResponse>('/ai/regenerate-text', body)

    // 自动开始追踪新任务
    trackGeneration(response.task_id, entityType, entityId, onComplete)

    return response.task_id
  }

  /**
   * 获取可用图片风格列表（对接 GET /api/v1/ai/styles）
   * 如果API不可用，使用默认风格列表
   */
  async function fetchStyles(): Promise<ImageStyle[]> {
    if (styles.value.length > 0) {
      return styles.value
    }

    stylesLoading.value = true
    try {
      const response = await get<StylesResponse>('/ai/styles')
      styles.value = response.styles
      return response.styles
    } catch {
      // API不可用时使用默认风格
      styles.value = DEFAULT_STYLES
      return DEFAULT_STYLES
    } finally {
      stylesLoading.value = false
    }
  }

  /**
   * 检查某个实体是否有正在进行的生成任务
   */
  function isGenerating(entityType: string, entityId: string): boolean {
    for (const task of pendingGenerations.value.values()) {
      if (
        task.entityType === entityType &&
        task.entityId === entityId &&
        (task.status === 'pending' || task.status === 'started')
      ) {
        return true
      }
    }
    return false
  }

  /**
   * 获取实体的生成状态
   */
  function getGenerationStatus(entityType: string, entityId: string): GenerationStatus | null {
    for (const task of pendingGenerations.value.values()) {
      if (task.entityType === entityType && task.entityId === entityId) {
        return task.status
      }
    }
    return null
  }

  /**
   * 清除所有轮询（组件卸载时调用）
   */
  function clearAll() {
    for (const task of pendingGenerations.value.values()) {
      if (task.timerId) {
        clearTimeout(task.timerId)
      }
    }
    pendingGenerations.value.clear()
  }

  return {
    // State
    pendingGenerations,
    styles,
    stylesLoading,
    // Polling & tracking
    trackGeneration,
    startPolling,
    stopPolling,
    checkStatus,
    // Regenerate
    regenerateImage,
    regenerateText,
    // Styles
    fetchStyles,
    // Helpers
    isGenerating,
    getGenerationStatus,
    clearAll,
  }
})
