// ============================================
// 日历模块 API
// ============================================

import { get, post, put, del } from '../request'
import type {
  CalendarEventItem,
  CalendarEventListResponse,
  CalendarEventCreateRequest,
  CalendarEventUpdateRequest,
} from '../types'

export const calendarApi = {
  /** 获取日历事件列表（分页，支持日期范围筛选） */
  getEvents(params: {
    page?: number
    page_size?: number
    start_date?: string
    end_date?: string
    event_type?: string
  } = {}): Promise<CalendarEventListResponse> {
    return get<CalendarEventListResponse>('/calendar/events', params)
  },

  /** 获取单个日历事件 */
  getEvent(id: string): Promise<CalendarEventItem> {
    return get<CalendarEventItem>(`/calendar/events/${id}`)
  },

  /** 创建日历事件 */
  createEvent(data: CalendarEventCreateRequest): Promise<CalendarEventItem> {
    return post<CalendarEventItem>('/calendar/events', data as unknown as Record<string, unknown>)
  },

  /** 更新日历事件 */
  updateEvent(id: string, data: CalendarEventUpdateRequest): Promise<CalendarEventItem> {
    return put<CalendarEventItem>(`/calendar/events/${id}`, data as unknown as Record<string, unknown>)
  },

  /** 删除日历事件 */
  deleteEvent(id: string): Promise<void> {
    return del<void>(`/calendar/events/${id}`)
  },

  /** 获取纪念日列表 */
  getAnniversaries(params: { page?: number; page_size?: number } = {}): Promise<CalendarEventListResponse> {
    return get<CalendarEventListResponse>('/calendar/anniversaries', params)
  },

  /** 创建纪念日 */
  createAnniversary(data: { title: string; event_date: string; remind_before_days?: number }): Promise<CalendarEventItem> {
    return post<CalendarEventItem>('/calendar/anniversaries', data as unknown as Record<string, unknown>)
  },
}
