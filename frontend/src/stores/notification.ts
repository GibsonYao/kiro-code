import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post } from '@/services/request'

/** 通知类型 */
export type NotificationType = 'task_remind' | 'review' | 'points' | 'anniversary' | 'system'

/** 通知项 */
export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  content: string
  is_read: boolean
  target_type?: string
  target_id?: string
  created_at: string
}

export const useNotificationStore = defineStore('notification', () => {
  // --- State ---
  const notifications = ref<NotificationItem[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)

  // --- Getters ---
  const unreadNotifications = computed(() =>
    notifications.value.filter(n => !n.is_read)
  )

  // --- Actions ---

  /** 获取通知列表 */
  async function fetchNotifications(type?: NotificationType): Promise<void> {
    loading.value = true
    try {
      const params: Record<string, unknown> = {}
      if (type) params.type = type
      const data = await get<{ items: NotificationItem[]; unread_count: number }>(
        '/notifications',
        params
      )
      notifications.value = data.items
      unreadCount.value = data.unread_count
    } catch {
      // Silently fail
    } finally {
      loading.value = false
    }
  }

  /** 获取未读数 */
  async function fetchUnreadCount(): Promise<void> {
    try {
      const data = await get<{ unread_count: number }>('/notifications/unread-count')
      unreadCount.value = data.unread_count
    } catch {
      // Silently fail
    }
  }

  /** 标记单条已读 */
  async function markAsRead(notificationId: string): Promise<void> {
    try {
      await post(`/notifications/${notificationId}/read`)
      const item = notifications.value.find(n => n.id === notificationId)
      if (item && !item.is_read) {
        item.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {
      // Silently fail
    }
  }

  /** 标记全部已读 */
  async function markAllAsRead(): Promise<void> {
    try {
      await post('/notifications/read-all')
      notifications.value.forEach(n => { n.is_read = true })
      unreadCount.value = 0
    } catch {
      // Silently fail
    }
  }

  return {
    // State
    notifications,
    unreadCount,
    loading,
    // Getters
    unreadNotifications,
    // Actions
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
  }
})
