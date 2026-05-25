// ============================================
// 审核模块 API
// ============================================

import { get, post } from '../request'
import type {
  ReviewItem,
  ReviewListResponse,
  ReviewApproveRequest,
  ReviewRejectRequest,
} from '../types'

export const reviewApi = {
  /** 获取待审核列表（分页） */
  getPendingReviews(params: { page?: number; page_size?: number } = {}): Promise<ReviewListResponse> {
    return get<ReviewListResponse>('/reviews/pending', params)
  },

  /** 通过审核 */
  approveReview(id: string, data?: ReviewApproveRequest): Promise<ReviewItem> {
    return post<ReviewItem>(`/reviews/${id}/approve`, data as unknown as Record<string, unknown>)
  },

  /** 驳回审核 */
  rejectReview(id: string, data?: ReviewRejectRequest): Promise<ReviewItem> {
    return post<ReviewItem>(`/reviews/${id}/reject`, data as unknown as Record<string, unknown>)
  },
}
