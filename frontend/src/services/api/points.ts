// ============================================
// 积分模块 API
// ============================================

import { get } from '../request'
import type {
  PointsBalanceResponse,
  PointsHistoryResponse,
  PointsLeaderboardResponse,
} from '../types'

export const pointsApi = {
  /** 获取积分余额 */
  getBalance(): Promise<PointsBalanceResponse> {
    return get<PointsBalanceResponse>('/points/balance')
  },

  /** 获取积分历史（分页） */
  getHistory(params: { page?: number; page_size?: number; type?: string } = {}): Promise<PointsHistoryResponse> {
    return get<PointsHistoryResponse>('/points/history', params as Record<string, unknown>)
  },

  /** 获取排行榜 */
  getLeaderboard(): Promise<PointsLeaderboardResponse> {
    return get<PointsLeaderboardResponse>('/points/leaderboard')
  },
}
