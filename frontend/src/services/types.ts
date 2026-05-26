// ============================================
// API 类型定义
// ============================================

/** 通用API响应 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 登录结果 */
export interface LoginResult {
  access_token: string
  refresh_token: string
  token_type: string
}

/** 用户信息 */
export interface UserInfo {
  id: string
  openid?: string
  phone?: string
  nickname: string
  avatar_url: string
  is_admin: boolean
  created_at: string
}

/** 家庭信息 */
export interface Family {
  id: string
  name: string
  avatar_url?: string
  invite_code: string
  role: 'admin' | 'member'
}

/** 获取当前用户信息响应 */
export interface MeResponse {
  user: UserInfo
  families: Family[]
}

/** 发送验证码请求 */
export interface SendCodeRequest {
  phone: string
}

/** 手机号登录请求 */
export interface PhoneLoginRequest {
  phone: string
  code: string
}

/** 微信登录请求 */
export interface WechatLoginRequest {
  code: string
}


// ============================================
// 愿望模块类型
// ============================================

/** 愿望状态 */
export type WishStatus = 'active' | 'achieved' | 'archived'

/** 愿望项 */
export interface WishItem {
  id: string
  family_id: string
  user_id: string
  title: string
  vision_story: string | null
  vision_image_url: string | null
  cover_image_url: string | null
  display_text: string | null
  status: WishStatus
  created_at: string
  updated_at: string
}

/** 愿望列表响应 */
export interface WishListResponse {
  items: WishItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 创建愿望请求 */
export interface WishCreateRequest {
  title: string
}


// ============================================
// 目标模块类型
// ============================================

/** 目标状态 */
export type GoalStatus = 'active' | 'completed' | 'archived'

/** 目标项 */
export interface GoalItem {
  id: string
  family_id: string
  wish_id: string | null
  user_id: string
  title: string
  description: string | null
  smart_specific: string | null
  smart_measurable: string | null
  smart_achievable: string | null
  smart_relevant: string | null
  smart_time_bound: string | null
  cover_image_url: string | null
  display_text: string | null
  progress: number
  status: GoalStatus
  owner_id: string
  created_at: string
  updated_at: string
}

/** 目标列表响应 */
export interface GoalListResponse {
  items: GoalItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 创建目标请求 */
export interface GoalCreateRequest {
  title: string
  description?: string
  wish_id?: string
}

/** 更新目标请求 */
export interface GoalUpdateRequest {
  title?: string
  description?: string
  status?: GoalStatus
  progress?: number
}

// ─── 链路视图类型 ─────────────────────────────────────────────────────────────

/** 链路中的愿望 */
export interface ChainWishItem {
  id: string
  title: string
  vision_story: string | null
  vision_image_url: string | null
  cover_image_url: string | null
  display_text: string | null
  status: string
}

/** 链路中的行动 */
export interface ChainActionItem {
  id: string
  title: string
  cover_image_url: string | null
  display_text: string | null
  action_type: string
  status: string
}

/** 链路中的任务 */
export interface ChainTaskItem {
  id: string
  title: string
  cover_image_url: string | null
  display_text: string | null
  task_type: string
  status: string
  reward_points: number
  penalty_points: number
  actions: ChainActionItem[]
}

/** 链路中的计划步骤 */
export interface ChainPlanStepItem {
  id: string
  title: string
  step_type: string
  is_bounty: boolean
  status: string
}

/** 链路中的计划 */
export interface ChainPlanItem {
  id: string
  title: string
  cover_image_url: string | null
  display_text: string | null
  status: string
  start_date: string | null
  end_date: string | null
  steps: ChainPlanStepItem[]
  tasks: ChainTaskItem[]
}

/** 目标链路响应 */
export interface GoalChainResponse {
  wish: ChainWishItem | null
  goal: GoalItem
  plans: ChainPlanItem[]
}


// ============================================
// 计划模块类型
// ============================================

/** 计划状态 */
export type PlanStatus = 'draft' | 'active' | 'completed' | 'overdue'

/** 步骤类型 */
export type StepType = 'task' | 'action'

/** 步骤状态 */
export type PlanStepStatus = 'pending' | 'in_progress' | 'completed'

/** 计划步骤 */
export interface PlanStepItem {
  id: string
  plan_id: string
  title: string
  step_type: StepType
  is_bounty: boolean
  sort_order: number
  status: PlanStepStatus
  created_at: string
  updated_at: string
}

/** 计划项 */
export interface PlanItem {
  id: string
  family_id: string
  goal_id: string | null
  title: string
  cover_image_url: string | null
  display_text: string | null
  start_date: string | null
  end_date: string | null
  owner_id: string
  status: PlanStatus
  created_at: string
  updated_at: string
  steps: PlanStepItem[]
}

/** 计划列表响应 */
export interface PlanListResponse {
  items: PlanItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 创建计划请求 */
export interface PlanCreateRequest {
  title: string
  goal_id?: string
  start_date?: string
  end_date?: string
  owner_id: string
}

/** 更新计划请求 */
export interface PlanUpdateRequest {
  title?: string
  start_date?: string
  end_date?: string
  owner_id?: string
  status?: PlanStatus
}

/** 创建步骤请求 */
export interface PlanStepCreateRequest {
  title: string
  step_type: StepType
  is_bounty?: boolean
  sort_order?: number
}

/** 更新步骤请求 */
export interface PlanStepUpdateRequest {
  title?: string
  step_type?: StepType
  is_bounty?: boolean
  sort_order?: number
  status?: PlanStepStatus
}


// ============================================
// 任务模块类型
// ============================================

/** 任务类型 */
export type TaskType = 'once' | 'recurring'

/** 任务状态 */
export type TaskStatus = 'pending' | 'claimed' | 'in_progress' | 'submitted' | 'approved' | 'rejected' | 'expired'

/** 任务项 */
export interface TaskItem {
  id: string
  family_id: string
  plan_step_id: string | null
  title: string
  description: string | null
  cover_image_url: string | null
  display_text: string | null
  task_type: TaskType
  recurrence_rule: Record<string, unknown> | null
  time_limit_hours: number | null
  reward_points: number
  penalty_points: number
  assignee_id: string | null
  status: TaskStatus
  deadline_at: string | null
  created_at: string
  updated_at: string
}

/** 任务列表响应 */
export interface TaskListResponse {
  items: TaskItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 创建任务请求 */
export interface TaskCreateRequest {
  title: string
  description?: string
  plan_step_id?: string
  task_type: TaskType
  recurrence_rule?: Record<string, unknown>
  time_limit_hours?: number
  reward_points?: number
  penalty_points?: number
  assignee_id?: string
}

/** 更新任务请求 */
export interface TaskUpdateRequest {
  title?: string
  description?: string
  task_type?: TaskType
  recurrence_rule?: Record<string, unknown>
  time_limit_hours?: number
  reward_points?: number
  penalty_points?: number
  assignee_id?: string
  status?: TaskStatus
}

/** 提交任务完成请求 */
export interface TaskSubmitRequest {
  evidence_text?: string
  evidence_photos?: string[]
  evidence_qrcode?: string
}


// ============================================
// 行动模块类型
// ============================================

/** 行动类型 */
export type ActionType = 'todo' | 'schedule'

/** 行动状态 */
export type ActionStatus = 'pending' | 'in_progress' | 'submitted' | 'approved' | 'rejected'

/** 行动项 */
export interface ActionItem {
  id: string
  family_id: string
  task_id: string | null
  plan_step_id: string | null
  user_id: string
  title: string
  cover_image_url: string | null
  display_text: string | null
  action_type: ActionType
  scheduled_date: string | null
  scheduled_time: string | null
  time_spent_minutes: number | null
  reward_points: number
  status: ActionStatus
  created_at: string
  updated_at: string
}

/** 行动列表响应 */
export interface ActionListResponse {
  items: ActionItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 创建行动请求 */
export interface ActionCreateRequest {
  title: string
  action_type: ActionType
  task_id?: string
  plan_step_id?: string
  scheduled_date?: string
  scheduled_time?: string
  reward_points?: number
}

/** 更新行动请求 */
export interface ActionUpdateRequest {
  title?: string
  action_type?: ActionType
  scheduled_date?: string
  scheduled_time?: string
  reward_points?: number
  status?: ActionStatus
}

/** 行动时间记录请求 */
export interface ActionTimeLogRequest {
  time_spent_minutes: number
}


// ============================================
// 食谱模块类型
// ============================================

/** 食谱项 */
export interface RecipeItem {
  id: string
  family_id: string
  name: string
  description: string | null
  cover_image_url: string | null
  display_text: string | null
  ingredients: string[] | null
  steps: string[] | null
  created_by: string
  created_at: string
  updated_at: string
}

/** 食谱列表响应 */
export interface RecipeListResponse {
  items: RecipeItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 创建食谱请求 */
export interface RecipeCreateRequest {
  name: string
  description?: string
  ingredients?: string[]
  steps?: string[]
}

/** 更新食谱请求 */
export interface RecipeUpdateRequest {
  name?: string
  description?: string
  ingredients?: string[]
  steps?: string[]
}

/** AI生成食谱响应 */
export interface RecipeGenerateResponse {
  id: string | null
  name: string
  ingredients: string[]
  steps: string[]
  description: string | null
}

/** 饮食偏好项 */
export interface FoodPreferenceItem {
  id: string
  family_id: string
  user_id: string
  taste_preferences: Record<string, unknown> | null
  favorite_foods: string[] | null
  food_allergies: string[] | null
  dietary_restrictions: string[] | null
  created_at: string
  updated_at: string
}

/** 饮食偏好汇总响应 */
export interface FoodPreferenceSummaryResponse {
  items: FoodPreferenceItem[]
  total: number
}

/** 更新饮食偏好请求 */
export interface FoodPreferenceUpdateRequest {
  taste_preferences?: Record<string, unknown>
  favorite_foods?: string[]
  food_allergies?: string[]
  dietary_restrictions?: string[]
}


// ============================================
// 日历模块类型
// ============================================

/** 日历事件类型 */
export type CalendarEventType = 'schedule' | 'todo' | 'anniversary'

/** 日历事件项 */
export interface CalendarEventItem {
  id: string
  family_id: string
  user_id: string
  title: string
  cover_image_url: string | null
  event_type: CalendarEventType
  event_date: string | null
  event_time: string | null
  is_recurring: boolean
  remind_before_days: number
  action_id: string | null
  created_at: string
  updated_at: string
}

/** 日历事件列表响应 */
export interface CalendarEventListResponse {
  items: CalendarEventItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 创建日历事件请求 */
export interface CalendarEventCreateRequest {
  title: string
  event_type: CalendarEventType
  event_date?: string
  event_time?: string
  is_recurring?: boolean
  remind_before_days?: number
}

/** 更新日历事件请求 */
export interface CalendarEventUpdateRequest {
  title?: string
  event_type?: CalendarEventType
  event_date?: string
  event_time?: string
  is_recurring?: boolean
  remind_before_days?: number
}


// ============================================
// 审核模块类型
// ============================================

/** 审核目标类型 */
export type ReviewTargetType = 'task' | 'action'

/** 审核状态 */
export type ReviewStatus = 'pending' | 'approved' | 'rejected'

/** 审核项 */
export interface ReviewItem {
  id: string
  family_id: string
  target_type: ReviewTargetType
  target_id: string
  reviewer_id: string
  submitter_id: string
  status: ReviewStatus
  comment: string | null
  evidence_text: string | null
  evidence_photos: string[] | null
  evidence_qrcode: string | null
  created_at: string
  updated_at: string
}

/** 审核列表响应 */
export interface ReviewListResponse {
  items: ReviewItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 审核通过请求 */
export interface ReviewApproveRequest {
  comment?: string
}

/** 审核驳回请求 */
export interface ReviewRejectRequest {
  comment?: string
}


// ============================================
// 积分模块类型
// ============================================

/** 积分交易类型 */
export type PointsTransactionType = 'reward' | 'penalty' | 'manual_adjust'

/** 积分余额响应 */
export interface PointsBalanceResponse {
  balance: number
  total_earned: number
  total_spent: number
}

/** 积分交易项 */
export interface PointsTransactionItem {
  id: string
  type: PointsTransactionType
  amount: number
  balance_after: number
  source_type: string | null
  source_id: string | null
  description: string | null
  created_at: string
}

/** 积分历史响应 */
export interface PointsHistoryResponse {
  items: PointsTransactionItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

/** 排行榜条目 */
export interface LeaderboardEntry {
  user_id: string
  nickname: string | null
  balance: number
  total_earned: number
}

/** 排行榜响应 */
export interface PointsLeaderboardResponse {
  items: LeaderboardEntry[]
}
