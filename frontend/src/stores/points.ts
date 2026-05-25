import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { pointsApi } from '@/services/api/points'
import type { PointsTransactionItem, LeaderboardEntry, PointsTransactionType } from '@/services/types'

export const usePointsStore = defineStore('points', () => {
  // --- State ---
  const balance = ref(0)
  const totalEarned = ref(0)
  const totalSpent = ref(0)

  const history = ref<PointsTransactionItem[]>([])
  const historyTotal = ref(0)
  const historyPage = ref(1)
  const historyPageSize = ref(20)
  const historyHasMore = ref(false)
  const historyType = ref<PointsTransactionType | undefined>(undefined)

  const leaderboard = ref<LeaderboardEntry[]>([])

  const loadingBalance = ref(false)
  const loadingHistory = ref(false)
  const loadingLeaderboard = ref(false)

  // --- Getters ---
  const isHistoryEmpty = computed(() => history.value.length === 0 && !loadingHistory.value)
  const isLeaderboardEmpty = computed(() => leaderboard.value.length === 0 && !loadingLeaderboard.value)

  // --- Actions ---

  /** 获取积分余额 */
  async function fetchBalance(): Promise<void> {
    loadingBalance.value = true
    try {
      const res = await pointsApi.getBalance()
      balance.value = res.balance
      totalEarned.value = res.total_earned
      totalSpent.value = res.total_spent
    } finally {
      loadingBalance.value = false
    }
  }

  /** 获取积分历史（首次加载或刷新） */
  async function fetchHistory(page = 1, type?: PointsTransactionType): Promise<void> {
    loadingHistory.value = true
    try {
      historyPage.value = page
      historyType.value = type
      const res = await pointsApi.getHistory({
        page,
        page_size: historyPageSize.value,
        type,
      })
      history.value = res.items
      historyTotal.value = res.total
      historyHasMore.value = res.has_more
    } finally {
      loadingHistory.value = false
    }
  }

  /** 加载更多历史记录 */
  async function loadMoreHistory(): Promise<void> {
    if (!historyHasMore.value || loadingHistory.value) return

    loadingHistory.value = true
    try {
      const nextPage = historyPage.value + 1
      const res = await pointsApi.getHistory({
        page: nextPage,
        page_size: historyPageSize.value,
        type: historyType.value,
      })
      history.value = [...history.value, ...res.items]
      historyPage.value = nextPage
      historyTotal.value = res.total
      historyHasMore.value = res.has_more
    } finally {
      loadingHistory.value = false
    }
  }

  /** 获取排行榜 */
  async function fetchLeaderboard(): Promise<void> {
    loadingLeaderboard.value = true
    try {
      const res = await pointsApi.getLeaderboard()
      leaderboard.value = res.items
    } finally {
      loadingLeaderboard.value = false
    }
  }

  /** 重置状态 */
  function reset(): void {
    balance.value = 0
    totalEarned.value = 0
    totalSpent.value = 0
    history.value = []
    historyTotal.value = 0
    historyPage.value = 1
    historyHasMore.value = false
    historyType.value = undefined
    leaderboard.value = []
    loadingBalance.value = false
    loadingHistory.value = false
    loadingLeaderboard.value = false
  }

  return {
    // State
    balance,
    totalEarned,
    totalSpent,
    history,
    historyTotal,
    historyHasMore,
    historyType,
    leaderboard,
    loadingBalance,
    loadingHistory,
    loadingLeaderboard,
    // Getters
    isHistoryEmpty,
    isLeaderboardEmpty,
    // Actions
    fetchBalance,
    fetchHistory,
    loadMoreHistory,
    fetchLeaderboard,
    reset,
  }
})
