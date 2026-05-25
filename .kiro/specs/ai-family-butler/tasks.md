# 实现任务清单：小灶AI家庭管家

## Phase 1：基础框架搭建

- [x] 1. 后端项目初始化与基础设施
  - [x] 1.1 创建FastAPI项目结构（app/main.py, core/, api/, models/, schemas/, services/, tasks/）
  - [x] 1.2 配置Pydantic Settings（数据库连接、Redis、OSS、JWT密钥等环境变量）
  - [x] 1.3 配置SQLAlchemy 2.0异步引擎和会话管理（core/deps.py）
  - [x] 1.4 初始化Alembic数据库迁移配置
  - [x] 1.5 配置Celery + Redis作为消息队列（tasks/__init__.py）
  - [x] 1.6 创建Docker Compose编排文件（PostgreSQL、Redis、FastAPI、Celery Worker、Celery Beat、Nginx）
  - [x] 1.7 配置Nginx反向代理（/api/* → FastAPI，/* → H5静态文件）

- [x] 2. 数据库模型定义与迁移
  - [x] 2.1 创建users表模型（UUID主键、openid、unionid、phone、nickname、avatar_url、is_admin）
  - [x] 2.2 创建families表模型（name、avatar_url、invite_code唯一、created_by外键）
  - [x] 2.3 创建family_members表模型（family_id、user_id、role枚举、nickname_in_family、relationship；联合唯一约束）
  - [x] 2.4 创建family_appellations表模型（from_member_id、to_member_id、appellation；联合唯一约束）
  - [x] 2.5 创建wishes表模型（family_id、user_id、title、vision_story、vision_image_url、cover_image_url、display_text、status枚举）
  - [x] 2.6 创建goals表模型（wish_id可空外键、title、description、smart_*五字段、cover_image_url、display_text、progress、status、owner_id）
  - [x] 2.7 创建plans表模型（goal_id可空外键、title、start_date、end_date、owner_id、status枚举）和plan_steps表模型（step_type、is_bounty、sort_order、status）
  - [x] 2.8 创建tasks表模型（plan_step_id可空、task_type枚举、recurrence_rule JSON、time_limit_hours、reward_points、penalty_points、assignee_id、status枚举、deadline_at）
  - [x] 2.9 创建actions表模型（task_id可空、plan_step_id可空、action_type枚举、scheduled_date、scheduled_time、time_spent_minutes、reward_points、status枚举）
  - [x] 2.10 创建reviews表模型（target_type枚举、target_id、reviewer_id、submitter_id、status枚举、evidence_text、evidence_photos JSON、evidence_qrcode）
  - [x] 2.11 创建points_accounts表模型（family_id+user_id联合唯一、balance允许负数、total_earned、total_spent）和points_transactions表模型（type枚举、amount、balance_after、source_type、source_id）
  - [x] 2.12 创建calendar_events表模型（event_type枚举、event_date、event_time、is_recurring、remind_before_days、action_id可空）
  - [x] 2.13 创建recipes表模型（name、description、ingredients JSON、steps JSON）和member_food_preferences表模型（taste_preferences JSON、favorite_foods JSON、food_allergies JSON、dietary_restrictions JSON）
  - [x] 2.14 创建ai_model_configs表模型（config_key、provider、model_name、api_key加密、api_base_url、parameters JSON、is_active、priority）
  - [x] 2.15 生成并执行Alembic初始迁移

- [x] 3. 用户认证模块（需求13）
  - [x] 3.1 实现JWT工具类（生成access_token/refresh_token、验证token、刷新逻辑）（core/security.py）
  - [x] 3.2 实现微信小程序登录接口（POST /api/v1/auth/wechat-login：code换取openid，查找或创建用户，返回JWT）
  - [x] 3.3 实现手机号+验证码登录接口（POST /api/v1/auth/send-code发送验证码、POST /api/v1/auth/phone-login验证并登录）
  - [x] 3.4 实现Token刷新接口（POST /api/v1/auth/refresh）
  - [x] 3.5 实现获取当前用户信息接口（GET /api/v1/auth/me）
  - [x] 3.6 实现认证依赖注入（core/deps.py：get_current_user、get_current_family）
  - [x] 3.7 实现数据权限中间件（验证请求中family_id归属当前用户）（需求16）

- [x] 4. 前端项目初始化
  - [x] 4.1 使用HBuilderX或CLI创建uni-app + Vue 3 + TypeScript项目
  - [x] 4.2 配置项目结构（pages/、components/、stores/、services/、composables/、utils/、platform/）
  - [x] 4.3 安装并配置uni-ui + uView Plus组件库
  - [x] 4.4 配置SCSS全局变量（主题色、圆角、阴影、间距等设计Token）
  - [x] 4.5 配置Pinia状态管理并实现UserStore（login、phoneLogin、switchFamily、logout）
  - [x] 4.6 实现API调用层封装（services/request.ts：拦截器、Token自动附加、刷新逻辑、错误处理）
  - [x] 4.7 实现登录页面（微信授权登录 + 手机号验证码登录切换）
  - [x] 4.8 实现路由守卫（未登录拦截跳转登录页）
  - [x] 4.9 配置pages.json页面路由和tabBar（首页、日历、食谱、我的）

## Phase 2：核心目标管理链路

- [x] 5. 愿望模块（需求2）
  - [x] 5.1 实现愿望CRUD后端接口（GET/POST /api/v1/wishes、GET/PUT/DELETE /api/v1/wishes/{id}）
  - [x] 5.2 实现愿望创建时触发AI生成愿景故事+愿景图的Celery异步任务
  - [x] 5.3 实现POST /api/v1/wishes/{id}/regenerate重新生成接口
  - [x] 5.4 实现前端WishStore（wishes列表、瀑布流分页、createWish、regenerateVision）
  - [x] 5.5 实现愿望列表页面（瀑布流布局 + 图文卡片展示愿景图和愿景故事）
  - [x] 5.6 实现愿望创建/编辑页面（标题输入、AI生成状态展示）

- [x] 6. 目标模块（需求3）
  - [x] 6.1 实现目标CRUD后端接口（GET/POST /api/v1/goals、GET/PUT/DELETE /api/v1/goals/{id}）
  - [x] 6.2 实现目标创建时AI生成SMART描述和配图的逻辑
  - [x] 6.3 实现GET /api/v1/goals/{id}/chain获取完整链路接口
  - [x] 6.4 实现前端GoalStore（goals列表、currentGoalChain、createGoal、fetchGoalChain）
  - [x] 6.5 实现目标列表页面（瀑布流 + 图文卡片展示配图、SMART描述、进度）
  - [x] 6.6 实现目标创建页面（标题、描述、关联愿望选择）
  - [x] 6.7 实现目标链路视图页面（展示愿望→目标→计划→任务→行动完整链路）

- [x] 7. 计划模块（需求4）
  - [x] 7.1 实现计划CRUD后端接口（GET/POST /api/v1/plans、GET/PUT/DELETE /api/v1/plans/{id}）
  - [x] 7.2 实现计划步骤管理接口（POST/PUT/DELETE /api/v1/plans/{id}/steps/{step_id}）
  - [x] 7.3 实现计划创建时校验负责人为当前家庭成员的逻辑
  - [x] 7.4 实现计划过期检查Celery Beat定时任务（每小时扫描overdue计划并通知）
  - [x] 7.5 实现前端计划列表和详情页面（图文卡片、步骤列表、悬赏/行动标记）
  - [x] 7.6 实现计划创建/编辑页面（标题、时间范围、负责人选择、步骤管理）

- [x] 8. 任务模块（需求5）
  - [x] 8.1 实现任务CRUD后端接口（GET/POST /api/v1/tasks、GET/PUT/DELETE /api/v1/tasks/{id}）
  - [x] 8.2 实现悬赏任务认领接口（POST /api/v1/tasks/{id}/claim，使用SELECT FOR UPDATE行级锁）
  - [x] 8.3 实现任务提交完成接口（POST /api/v1/tasks/{id}/submit，附带验证要素：文字/照片/扫码）
  - [x] 8.4 实现GET /api/v1/tasks/bounty可认领悬赏任务列表接口
  - [x] 8.5 实现任务超时惩罚Celery Beat定时任务（每10分钟扫描expired任务，自动扣除积分）
  - [x] 8.6 实现重复任务自动生成Celery Beat定时任务（每天凌晨扫描已完成的recurring任务，生成下一周期）
  - [x] 8.7 实现前端TaskStore（myTasks、bountyTasks、pendingReviews、claimTask、submitTask）
  - [x] 8.8 实现任务列表页面（我的任务/悬赏任务切换、图文卡片展示）
  - [x] 8.9 实现任务创建页面（类型选择、时限、积分奖惩设置、关联计划）
  - [x] 8.10 实现任务完成提交页面（完成验证器：文字描述、照片上传、扫码验证）

- [x] 9. 行动模块（需求6）
  - [x] 9.1 实现行动CRUD后端接口（GET/POST /api/v1/actions、GET/PUT/DELETE /api/v1/actions/{id}）
  - [x] 9.2 实现行动完成接口（POST /api/v1/actions/{id}/complete）和时间记录接口（PUT /api/v1/actions/{id}/time-log）
  - [x] 9.3 实现行动完成后自动更新关联任务进度的逻辑
  - [x] 9.4 实现前端行动列表页面（待办/日程分类、图文卡片、时间记录）
  - [x] 9.5 实现行动创建页面（类型选择：待办/日程、日期时间设置、关联任务）

- [x] 10. 审核流程（需求5.8-13、需求6.8-12）
  - [x] 10.1 实现审核服务层（确定审核人逻辑：计划负责人 > 目标负责人 > 家庭管理员）
  - [x] 10.2 实现审核接口（GET /api/v1/reviews/pending、POST /api/v1/reviews/{id}/approve、POST /api/v1/reviews/{id}/reject）
  - [x] 10.3 实现审核通过后触发积分发放和链路状态传播的逻辑
  - [x] 10.4 实现审核驳回后状态回退和通知执行人的逻辑
  - [x] 10.5 实现前端审核列表页面和审核操作界面

- [ ] 11. 积分系统（需求7）
  - [x] 11.1 实现积分账户服务（创建账户、查询余额、增加/扣除积分、记录流水）
  - [x] 11.2 实现积分接口（GET /api/v1/points/balance、GET /api/v1/points/history支持筛选、GET /api/v1/points/leaderboard）
  - [x] 11.3 实现前端PointsStore（balance、history、leaderboard）
  - [x] 11.4 实现积分主页展示（余额卡片、历史时间线、排行榜）

- [ ] 12. 目标管理链路状态传播（需求11）
  - [x] 12.1 实现链路状态向上传播服务（行动完成→任务进度→计划完成→目标进度）
  - [x] 12.2 实现删除有下游关联条目时的确认和关联解除逻辑
  - [x] 12.3 实现前端链路视图组件（图文并茂展示上下游关联条目）

## Phase 3：AI集成

- [ ] 13. AI服务适配层（需求1、需求14）
  - [x] 13.1 实现AIServiceAdapter类（统一调用接口、工厂模式路由到供应商）
  - [x] 13.2 实现DashScopeProvider（通义千问文案生成、通义万相图片生成）
  - [x] 13.3 实现DeepSeekProvider（文案生成备选）
  - [x] 13.4 实现OpenAICompatibleProvider（兼容接口）
  - [x] 13.5 实现StableDiffusionProvider（图片生成备选）
  - [x] 13.6 实现配置缓存机制（Redis缓存活跃配置，TTL 5分钟，变更时失效）
  - [x] 13.7 实现Fallback机制（按priority排序，主模型失败自动切换备用）
  - [x] 13.8 实现AI生成Celery异步任务（文案生成任务、图片生成任务、愿景故事生成任务）
  - [x] 13.9 实现AI生成状态查询接口（GET /api/v1/ai/generation/{task_id}/status）
  - [x] 13.10 实现图片上传至阿里云OSS的工具函数
  - [x] 13.11 实现AI生成失败降级处理（使用默认占位图+原始文案）

- [ ] 14. 后台管理系统（需求14）
  - [-] 14.1 实现AI模型配置CRUD接口（GET/POST/PUT/DELETE /api/v1/admin/ai-configs）
  - [~] 14.2 实现模型连通性测试接口（POST /api/v1/admin/ai-configs/{id}/test）
  - [~] 14.3 实现配置激活/停用接口（PUT /api/v1/admin/ai-configs/{id}/activate）
  - [~] 14.4 实现API Key AES-256加密存储和前端脱敏显示
  - [~] 14.5 实现配置变更操作日志记录
  - [~] 14.6 实现管理员权限校验中间件（仅is_admin=true可访问）
  - [~] 14.7 实现前端后台管理页面（AI模型配置列表、新增/编辑表单、测试连接、fallback排序）

- [ ] 15. 前端AI生成状态集成
  - [~] 15.1 实现AIStatusStore（pendingGenerations Map、轮询状态、生成完成回调）
  - [~] 15.2 实现图文卡片组件（展示AI配图+文案、加载态、失败重试按钮）
  - [~] 15.3 实现重新生成配图/文案的前端交互（POST /api/v1/ai/regenerate-image、regenerate-text）
  - [~] 15.4 实现图片风格选择组件（GET /api/v1/ai/styles获取可用风格列表）

## Phase 4：辅助模块

- [ ] 16. 日历模块（需求8）
  - [~] 16.1 实现日历事件CRUD后端接口（GET/POST/PUT/DELETE /api/v1/calendar/events按日期范围查询）
  - [~] 16.2 实现纪念日管理接口（GET/POST /api/v1/calendar/anniversaries）
  - [~] 16.3 实现日历创建日程时自动同步为行动模块日程类型行动的逻辑
  - [~] 16.4 实现纪念日提醒Celery Beat定时任务（提前N天发送通知）
  - [~] 16.5 实现前端日历页面（日视图/月视图切换、快速记录日程/待办入口）
  - [~] 16.6 实现纪念日管理页面（添加/编辑纪念日、AI生成祝福文案和配图）

- [ ] 17. 食谱模块（需求9）
  - [~] 17.1 实现食谱CRUD后端接口（GET/POST/PUT/DELETE /api/v1/recipes）
  - [~] 17.2 实现饮食偏好接口（GET /api/v1/recipes/preferences汇总、PUT /api/v1/recipes/preferences/{user_id}更新）
  - [~] 17.3 实现前端食谱列表页面（瀑布流图文卡片、AI菜品图展示）
  - [~] 17.4 实现食谱添加/编辑页面（菜品名称、描述、食材、步骤）
  - [~] 17.5 实现家庭成员饮食偏好设置页面（口味偏好、喜好、禁忌）

- [ ] 18. 家庭成员管理模块（需求10）
  - [~] 18.1 实现家庭CRUD接口（POST /api/v1/families创建、GET /api/v1/families/current、POST /api/v1/families/join邀请码加入）
  - [~] 18.2 实现家庭成员管理接口（GET/POST /api/v1/families/members、PUT /api/v1/families/members/{id}/appellation设置称谓）
  - [~] 18.3 实现家庭视角切换接口（PUT /api/v1/families/switch/{family_id}）和称谓关系计算逻辑
  - [~] 18.4 实现防重复添加成员校验（UNIQUE约束 + 接口层校验）
  - [~] 18.5 实现前端家庭成员页面（图文卡片展示、当前视角称谓、添加成员、切换家庭）

## Phase 5：体验优化

- [ ] 19. 通知推送系统（需求15）
  - [~] 19.1 实现统一通知服务NotificationService（根据用户渠道选择推送方式）
  - [~] 19.2 实现微信订阅消息推送（任务提醒、审核通知、积分变动、纪念日提醒模板）
  - [~] 19.3 实现站内通知表和接口（通知列表、未读角标、标记已读）
  - [~] 19.4 实现Web Push API + Service Worker推送（降级为站内通知）
  - [~] 19.5 实现前端通知中心页面（通知列表、未读标记、点击跳转）

- [ ] 20. UI体验优化（需求12）
  - [~] 20.1 实现瀑布流布局组件（多列不等高、响应式适配）
  - [~] 20.2 实现统一图文卡片组件（圆角、阴影、配图+文案、加载骨架屏）
  - [~] 20.3 实现首页瀑布流（展示最近的愿望、目标、任务混合流）
  - [~] 20.4 实现深色模式/浅色模式切换（CSS变量方案、图文展示适配）
  - [~] 20.5 实现模块引导页面（首次进入时展示视觉冲击力引导）

- [ ] 21. 数据权限与安全加固（需求16、需求17）
  - [~] 21.1 实现所有API的家庭数据隔离中间件（请求级family_id校验）
  - [~] 21.2 实现条目删除权限校验（仅创建者或家庭管理员可删除）
  - [~] 21.3 实现敏感信息加密存储工具（AES-256加密/解密API Key等）
  - [~] 21.4 配置HTTPS和安全响应头
  - [~] 21.5 实现API响应时间监控和性能优化（确保普通请求<500ms）
