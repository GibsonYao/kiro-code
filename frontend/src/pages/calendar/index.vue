<template>
  <view class="calendar-page">
    <!-- 视图切换 + 月份导航 -->
    <view class="top-bar">
      <view class="view-toggle">
        <view
          class="toggle-item"
          :class="{ active: viewMode === 'month' }"
          @click="viewMode = 'month'"
        >
          <text>月视图</text>
        </view>
        <view
          class="toggle-item"
          :class="{ active: viewMode === 'day' }"
          @click="viewMode = 'day'"
        >
          <text>日视图</text>
        </view>
      </view>
    </view>

    <!-- 月份切换 -->
    <view class="month-header">
      <view class="month-nav" @click="prevMonth">
        <text class="nav-arrow">‹</text>
      </view>
      <text class="month-title">{{ currentYear }}年{{ currentMonth }}月</text>
      <view class="month-nav" @click="nextMonth">
        <text class="nav-arrow">›</text>
      </view>
    </view>

    <!-- 月视图：日历网格 -->
    <view v-if="viewMode === 'month'">
      <!-- 星期标题 -->
      <view class="weekday-row">
        <text v-for="day in weekDays" :key="day" class="weekday-item">{{ day }}</text>
      </view>

      <!-- 日历网格 -->
      <view class="calendar-grid">
        <view
          v-for="(cell, idx) in calendarCells"
          :key="idx"
          class="calendar-cell"
          :class="{
            'other-month': !cell.isCurrentMonth,
            'is-today': cell.isToday,
            'has-events': cell.eventCount > 0,
            'selected': cell.dateStr === selectedDate,
          }"
          @click="selectDate(cell)"
        >
          <text class="cell-day">{{ cell.day }}</text>
          <view v-if="cell.eventCount > 0" class="event-dot"></view>
        </view>
      </view>
    </view>

    <!-- 日视图：选中日期详情 -->
    <view v-if="viewMode === 'day'" class="day-view-header">
      <view class="day-nav" @click="prevDay">
        <text class="nav-arrow">‹</text>
      </view>
      <text class="day-title">{{ formatSelectedDate(selectedDate) }}</text>
      <view class="day-nav" @click="nextDay">
        <text class="nav-arrow">›</text>
      </view>
    </view>

    <!-- 选中日期的事件列表 -->
    <view class="events-section">
      <view class="events-header">
        <text class="events-title">
          {{ formatSelectedDate(selectedDate) }} 事件
        </text>
        <view class="header-actions">
          <view class="anniversary-link" @click="goAnniversary">
            <text class="anniversary-text">🎂 纪念日</text>
          </view>
        </view>
      </view>

      <!-- 快速添加入口 -->
      <view class="quick-add-row">
        <view class="quick-add-btn" @click="quickAdd('schedule')">
          <text class="quick-icon">📅</text>
          <text class="quick-label">记日程</text>
        </view>
        <view class="quick-add-btn" @click="quickAdd('todo')">
          <text class="quick-icon">✅</text>
          <text class="quick-label">记待办</text>
        </view>
        <view class="quick-add-btn" @click="goCreate">
          <text class="quick-icon">➕</text>
          <text class="quick-label">新建</text>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="loading" class="loading-state">
        <text>加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="dayEvents.length === 0" class="empty-state">
        <text class="empty-text">暂无事件</text>
        <text class="empty-hint">点击上方按钮快速添加日程或待办</text>
      </view>

      <!-- 事件列表 -->
      <view v-else class="event-list">
        <view
          v-for="event in dayEvents"
          :key="event.id"
          class="event-card"
          @click="goDetail(event.id)"
        >
          <view class="event-type-indicator" :class="'type-' + event.event_type"></view>
          <view class="event-info">
            <text class="event-title">{{ event.title }}</text>
            <view class="event-meta">
              <text class="event-type-label">{{ eventTypeLabel(event.event_type) }}</text>
              <text v-if="event.event_time" class="event-time">{{ event.event_time }}</text>
              <text v-if="event.is_recurring" class="event-recurring">🔄 重复</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { calendarApi } from '@/services/api/calendar'
import { checkAuth } from '@/utils/route-guard'
import type { CalendarEventItem, CalendarEventType } from '@/services/types'

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const viewMode = ref<'month' | 'day'>('month')
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const selectedDate = ref(formatDateStr(new Date()))
const events = ref<CalendarEventItem[]>([])
const loading = ref(false)

interface CalendarCell {
  day: number
  dateStr: string
  isCurrentMonth: boolean
  isToday: boolean
  eventCount: number
}

const calendarCells = computed<CalendarCell[]>(() => {
  const cells: CalendarCell[] = []
  const year = currentYear.value
  const month = currentMonth.value

  const firstDay = new Date(year, month - 1, 1)
  const startWeekday = firstDay.getDay()
  const daysInMonth = new Date(year, month, 0).getDate()
  const prevMonthDays = new Date(year, month - 1, 0).getDate()
  const today = formatDateStr(new Date())

  for (let i = startWeekday - 1; i >= 0; i--) {
    const day = prevMonthDays - i
    const m = month === 1 ? 12 : month - 1
    const y = month === 1 ? year - 1 : year
    const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    cells.push({ day, dateStr, isCurrentMonth: false, isToday: dateStr === today, eventCount: getEventCount(dateStr) })
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    cells.push({ day, dateStr, isCurrentMonth: true, isToday: dateStr === today, eventCount: getEventCount(dateStr) })
  }

  const remaining = 42 - cells.length
  for (let day = 1; day <= remaining; day++) {
    const m = month === 12 ? 1 : month + 1
    const y = month === 12 ? year + 1 : year
    const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    cells.push({ day, dateStr, isCurrentMonth: false, isToday: dateStr === today, eventCount: getEventCount(dateStr) })
  }

  return cells
})

const dayEvents = computed(() => {
  return events.value.filter(e => e.event_date === selectedDate.value)
})

function getEventCount(dateStr: string): number {
  return events.value.filter(e => e.event_date === dateStr).length
}

function formatDateStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatSelectedDate(dateStr: string): string {
  const parts = dateStr.split('-')
  return `${parseInt(parts[1])}月${parseInt(parts[2])}日`
}

function prevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function prevDay() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() - 1)
  selectedDate.value = formatDateStr(d)
  // Update month if needed
  currentYear.value = d.getFullYear()
  currentMonth.value = d.getMonth() + 1
}

function nextDay() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() + 1)
  selectedDate.value = formatDateStr(d)
  currentYear.value = d.getFullYear()
  currentMonth.value = d.getMonth() + 1
}

function selectDate(cell: CalendarCell) {
  selectedDate.value = cell.dateStr
}

async function fetchMonthEvents() {
  loading.value = true
  try {
    const year = currentYear.value
    const month = currentMonth.value
    const startDate = `${year}-${String(month).padStart(2, '0')}-01`
    const daysInMonth = new Date(year, month, 0).getDate()
    const endDate = `${year}-${String(month).padStart(2, '0')}-${String(daysInMonth).padStart(2, '0')}`

    const res = await calendarApi.getEvents({
      start_date: startDate,
      end_date: endDate,
      page_size: 100,
    })
    events.value = res.items
  } catch {
    events.value = []
  } finally {
    loading.value = false
  }
}

function eventTypeLabel(type: CalendarEventType): string {
  const map: Record<CalendarEventType, string> = {
    schedule: '📅 日程',
    todo: '✅ 待办',
    anniversary: '🎂 纪念日',
  }
  return map[type] || type
}

function quickAdd(type: 'schedule' | 'todo') {
  uni.navigateTo({ url: `/pages/calendar/create?date=${selectedDate.value}&type=${type}` })
}

function goCreate() {
  uni.navigateTo({ url: `/pages/calendar/create?date=${selectedDate.value}` })
}

function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/calendar/create?id=${id}` })
}

function goAnniversary() {
  uni.navigateTo({ url: '/pages/calendar/anniversary' })
}

onMounted(() => {
  fetchMonthEvents()
})

onShow(() => {
  checkAuth()
  fetchMonthEvents()
})

watch([currentYear, currentMonth], () => {
  fetchMonthEvents()
})
</script>

<style lang="scss" scoped>
.calendar-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 32rpx;
  background: #fff;
}

.view-toggle {
  display: flex;
  background: #f0f0f5;
  border-radius: 8rpx;
  overflow: hidden;
}

.toggle-item {
  padding: 12rpx 32rpx;
  font-size: 26rpx;
  color: #666;
  transition: all 0.2s;

  &.active {
    background: #4a90d9;
    color: #fff;
    border-radius: 8rpx;
  }
}

.month-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 32rpx;
  background: #fff;
}

.month-nav {
  padding: 16rpx 24rpx;
}

.nav-arrow {
  font-size: 40rpx;
  color: #4a90d9;
  font-weight: 600;
}

.month-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin: 0 32rpx;
}

.day-view-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 32rpx;
  background: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}

.day-nav {
  padding: 16rpx 24rpx;
}

.day-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #333;
  margin: 0 48rpx;
}

.weekday-row {
  display: flex;
  background: #fff;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.weekday-item {
  flex: 1;
  text-align: center;
  font-size: 24rpx;
  color: #999;
}

.calendar-grid {
  display: flex;
  flex-wrap: wrap;
  background: #fff;
  padding-bottom: 16rpx;
}

.calendar-cell {
  width: calc(100% / 7);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 0;
  position: relative;

  &.other-month .cell-day {
    color: #ccc;
  }

  &.is-today .cell-day {
    background: #4a90d9;
    color: #fff;
    border-radius: 50%;
    width: 56rpx;
    height: 56rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &.selected {
    background: #f0f7ff;
  }

  &.selected .cell-day {
    font-weight: 600;
    color: #4a90d9;
  }

  &.is-today.selected .cell-day {
    color: #fff;
  }
}

.cell-day {
  font-size: 28rpx;
  color: #333;
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.event-dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #f5222d;
  margin-top: 4rpx;
}

.events-section {
  margin-top: 16rpx;
  background: #fff;
  padding: 24rpx 32rpx;
  min-height: 300rpx;
}

.events-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.events-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
}

.anniversary-link {
  padding: 8rpx 16rpx;
  background: #fff7e6;
  border-radius: 20rpx;
}

.anniversary-text {
  font-size: 24rpx;
  color: #fa8c16;
}

.quick-add-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.quick-add-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
  background: #f9f9fb;
  border-radius: 12rpx;
  border: 1rpx solid #e8e8e8;
}

.quick-icon {
  font-size: 36rpx;
  margin-bottom: 8rpx;
}

.quick-label {
  font-size: 22rpx;
  color: #666;
}

.loading-state {
  text-align: center;
  padding: 48rpx;
  color: #999;
  font-size: 26rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48rpx 0;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 8rpx;
}

.empty-hint {
  font-size: 24rpx;
  color: #ccc;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.event-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.event-type-indicator {
  width: 8rpx;
  height: 64rpx;
  border-radius: 4rpx;
  margin-right: 20rpx;

  &.type-schedule {
    background: #4a90d9;
  }
  &.type-todo {
    background: #52c41a;
  }
  &.type-anniversary {
    background: #fa8c16;
  }
}

.event-info {
  flex: 1;
}

.event-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.event-type-label {
  font-size: 22rpx;
  color: #666;
}

.event-time {
  font-size: 22rpx;
  color: #4a90d9;
}

.event-recurring {
  font-size: 22rpx;
  color: #fa8c16;
}
</style>
