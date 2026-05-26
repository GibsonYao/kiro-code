import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { calendarApi } from '@/services/api/calendar'
import type { CalendarEventItem, CalendarEventCreateRequest } from '@/services/types'

export const useCalendarStore = defineStore('calendar', () => {
  // --- State ---
  const events = ref<CalendarEventItem[]>([])
  const anniversaries = ref<CalendarEventItem[]>([])
  const loading = ref(false)
  const creating = ref(false)

  // --- Getters ---
  const isEmpty = computed(() => events.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 按日期范围查询事件 */
  async function fetchEvents(params: {
    start_date?: string
    end_date?: string
    event_type?: string
    page_size?: number
  } = {}): Promise<void> {
    loading.value = true
    try {
      const res = await calendarApi.getEvents({
        page_size: params.page_size || 100,
        ...params,
      })
      events.value = res.items
    } catch {
      events.value = []
    } finally {
      loading.value = false
    }
  }

  /** 获取纪念日列表 */
  async function fetchAnniversaries(): Promise<void> {
    loading.value = true
    try {
      const res = await calendarApi.getAnniversaries({ page_size: 100 })
      anniversaries.value = res.items
    } catch {
      anniversaries.value = []
    } finally {
      loading.value = false
    }
  }

  /** 创建事件 */
  async function createEvent(data: CalendarEventCreateRequest): Promise<CalendarEventItem> {
    creating.value = true
    try {
      const event = await calendarApi.createEvent(data)
      events.value.unshift(event)
      if (data.event_type === 'anniversary') {
        anniversaries.value.unshift(event)
      }
      return event
    } finally {
      creating.value = false
    }
  }

  /** 更新事件 */
  async function updateEvent(id: string, data: Partial<CalendarEventCreateRequest>): Promise<CalendarEventItem> {
    const event = await calendarApi.updateEvent(id, data)
    const idx = events.value.findIndex(e => e.id === id)
    if (idx !== -1) events.value[idx] = event
    const aIdx = anniversaries.value.findIndex(e => e.id === id)
    if (aIdx !== -1) anniversaries.value[aIdx] = event
    return event
  }

  /** 删除事件 */
  async function deleteEvent(id: string): Promise<void> {
    await calendarApi.deleteEvent(id)
    events.value = events.value.filter(e => e.id !== id)
    anniversaries.value = anniversaries.value.filter(e => e.id !== id)
  }

  /** 按日期获取事件 */
  function getEventsByDate(dateStr: string): CalendarEventItem[] {
    return events.value.filter(e => e.event_date === dateStr)
  }

  /** 重置状态 */
  function reset(): void {
    events.value = []
    anniversaries.value = []
    loading.value = false
    creating.value = false
  }

  return {
    // State
    events,
    anniversaries,
    loading,
    creating,
    // Getters
    isEmpty,
    // Actions
    fetchEvents,
    fetchAnniversaries,
    createEvent,
    updateEvent,
    deleteEvent,
    getEventsByDate,
    reset,
  }
})
