// ============================================
// 愿望模块 API
// ============================================

import { get, post, put, del } from '../request'
import type { WishItem, WishListResponse, WishCreateRequest } from '../types'

export const wishApi = {
  /** 获取愿望列表（分页） */
  getWishes(params: { page?: number; page_size?: number; status?: string } = {}): Promise<WishListResponse> {
    return get<WishListResponse>('/wishes', params)
  },

  /** 获取单个愿望详情 */
  getWish(id: string): Promise<WishItem> {
    return get<WishItem>(`/wishes/${id}`)
  },

  /** 创建愿望 */
  createWish(data: WishCreateRequest): Promise<WishItem> {
    return post<WishItem>('/wishes', data as unknown as Record<string, unknown>)
  },

  /** 更新愿望 */
  updateWish(id: string, data: { title?: string; status?: string }): Promise<WishItem> {
    return put<WishItem>(`/wishes/${id}`, data)
  },

  /** 删除愿望 */
  deleteWish(id: string): Promise<void> {
    return del<void>(`/wishes/${id}`)
  },

  /** 重新生成愿景故事和图片 */
  regenerateVision(id: string): Promise<WishItem> {
    return post<WishItem>(`/wishes/${id}/regenerate`)
  },
}
