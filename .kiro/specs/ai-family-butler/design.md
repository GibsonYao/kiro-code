# 技术设计文档：小灶AI家庭管家

## 概述（Overview）

小灶AI家庭管家是一款AI原生家庭管理应用，采用前后端分离架构，支持**微信小程序**和**Web端**两种使用方式。系统核心围绕"愿望 → 目标 → 计划 → 任务 → 行动"的完整目标管理链路，结合AI图文生成能力，为家庭成员提供极具视觉吸引力的目标追踪和激励体验。

### 核心设计目标

1. **AI原生体验**：所有内容创建均伴随AI配图和文案生成，打造图文并茂的视觉效果
2. **跨平台共享代码**：微信小程序 + Web端共享核心业务逻辑和UI组件
3. **链路完整性**：维护从愿望到行动的完整关联链路，支持自动状态传播
4. **激励机制**：通过积分奖惩和审核机制，激励家庭成员持续执行
5. **多家庭视角**：支持成员在不同家庭间切换视角，正确展示称谓关系

### 技术选型

| 层级 | 技术选择 | 理由 |
|------|----------|------|
| 跨平台框架 | uni-app + Vue 3 + TypeScript | 一套代码编译到微信小程序和H5 Web端 |
| 状态管理 | Pinia | Vue 3官方推荐，TypeScript友好 |
| UI组件库 | uni-ui + uView Plus | 多端适配完善 |
| 样式方案 | SCSS | uni-app原生支持 |
| 后端框架 | FastAPI (Python) | 异步原生支持，AI生态无缝集成 |
| 数据库 | PostgreSQL | 关系型数据，支持复杂查询和JSON字段 |
| ORM | SQLAlchemy 2.0 + Alembic | 异步支持，Alembic管理迁移 |
| 缓存 | Redis | 积分排行榜、会话管理、AI任务队列 |
| AI图片生成 | 通义万相 / Stable Diffusion API | 国内可用、支持多风格 |
| AI文案生成 | 通义千问 / DeepSeek API | 中文能力强、成本可控 |
| AI集成框架 | LangChain + dashscope SDK | Python原生AI生态 |
| 对象存储 | 阿里云OSS | 存储AI生成图片和用户上传照片 |
| 消息队列 | Celery + Redis | AI生成任务异步处理、通知推送 |
| 推送服务 | 微信订阅消息 + Web Push API | 小程序+Web端推送 |
| 认证 | 微信登录 + JWT (python-jose) | 小程序微信授权，Web端手机号+验证码 |

### 项目结构

```
├── frontend/                    # uni-app前端项目
│   ├── src/
│   │   ├── pages/              # 页面组件（跨端共享）
│   │   ├── components/         # UI组件（跨端共享）
│   │   ├── stores/             # Pinia状态管理
│   │   ├── services/           # API调用层
│   │   ├── composables/        # Vue 3组合式函数
│   │   ├── utils/              # 工具函数
│   │   └── platform/           # 平台差异化代码（weapp/ h5/）
│   └── package.json
│
└── backend/                     # FastAPI后端项目
    ├── app/
    │   ├── main.py             # FastAPI应用入口
    │   ├── core/               # 核心配置（config, security, deps）
    │   ├── api/v1/             # API路由（按模块划分）
    │   ├── models/             # SQLAlchemy模型
    │   ├── schemas/            # Pydantic请求/响应模型
    │   ├── services/           # 业务逻辑层
    │   └── tasks/              # Celery异步任务
    ├── alembic/                # 数据库迁移
    └── tests/
```

## 后台管理系统：AI模型配置

### 设计目标

提供后台管理页面，允许管理员在运行时动态配置和切换AI模型供应商、API密钥和参数，无需重启服务。

### 核心数据模型

AIModelConfig表：config_key（text_generation/image_generation/vision_story）、provider（dashscope/deepseek/openai/stable_diffusion）、model_name、api_key（AES-256加密）、api_base_url、parameters（JSON）、is_active、priority（fallback优先级）

### API接口

- GET/POST/PUT/DELETE `/api/v1/admin/ai-configs` — CRUD操作
- POST `/api/v1/admin/ai-configs/{id}/test` — 测试模型连通性
- PUT `/api/v1/admin/ai-configs/{id}/activate` — 激活/停用配置

### 核心机制

1. **加密存储**：API Key使用AES-256加密，前端脱敏显示
2. **配置缓存**：活跃配置缓存到Redis，TTL 5分钟，变更时主动失效
3. **Fallback机制**：按priority排序，主模型失败时自动切换备用模型
4. **AI服务适配层**：AIServiceAdapter统一调用接口，工厂模式路由到对应供应商
5. **操作审计**：所有配置变更记录操作日志

## 数据库模型设计

### ER关系概览

```
User → 1:N → FamilyMember → N:1 → Family
User → 1:N → Wish → 1:N → Goal → 1:N → Plan → 1:N → PlanStep → Task/Action
User → 1:N → PointsAccount → 1:N → PointsTransaction
User → 1:N → Review
```

### 核心表

- **users**: id(UUID), openid, unionid, phone, nickname, avatar_url, is_admin
- **families**: id, name, avatar_url, invite_code(唯一), created_by
- **family_members**: id, family_id, user_id, role(admin/member), nickname_in_family, relationship; UNIQUE(family_id, user_id)
- **family_appellations**: id, family_id, from_member_id, to_member_id, appellation; UNIQUE(family_id, from, to)
- **wishes**: id, family_id, user_id, title, vision_story, vision_image_url, cover_image_url, display_text, status(active/achieved/archived)
- **goals**: id, family_id, wish_id(可空), user_id, title, description, smart_*(5字段), cover_image_url, display_text, progress(0-100), status, owner_id
- **plans**: id, family_id, goal_id(可空), title, cover_image_url, display_text, start_date, end_date, owner_id, status(draft/active/completed/overdue)
- **plan_steps**: id, plan_id, title, step_type(task/action), is_bounty, sort_order, status
- **tasks**: id, family_id, plan_step_id(可空), title, description, cover_image_url, display_text, task_type(once/recurring), recurrence_rule(JSON), time_limit_hours, reward_points, penalty_points, assignee_id, status(pending/claimed/in_progress/submitted/approved/rejected/expired), deadline_at
- **actions**: id, family_id, task_id(可空), plan_step_id(可空), user_id, title, cover_image_url, display_text, action_type(todo/schedule), scheduled_date, scheduled_time, time_spent_minutes, reward_points, status(pending/in_progress/submitted/approved/rejected)
- **reviews**: id, family_id, target_type(task/action), target_id, reviewer_id, submitter_id, status(pending/approved/rejected), comment, evidence_text, evidence_photos(JSON), evidence_qrcode
- **points_accounts**: id, family_id, user_id, balance(允许负数), total_earned, total_spent; UNIQUE(family_id, user_id)
- **points_transactions**: id, account_id, type(reward/penalty/manual_adjust), amount, balance_after, source_type, source_id, description
- **calendar_events**: id, family_id, user_id, title, cover_image_url, event_type(schedule/todo/anniversary), event_date, event_time, is_recurring, remind_before_days, action_id(可空)
- **recipes**: id, family_id, name, description, cover_image_url, display_text, ingredients(JSON), steps(JSON), created_by
- **member_food_preferences**: id, family_id, user_id, taste_preferences(JSON), favorite_foods(JSON), food_allergies(JSON), dietary_restrictions(JSON)

## API接口设计

### 认证模块
- POST `/api/v1/auth/wechat-login` — 微信小程序登录
- POST `/api/v1/auth/phone-login` — 手机号+验证码登录
- POST `/api/v1/auth/send-code` — 发送短信验证码
- POST `/api/v1/auth/refresh` — 刷新Token
- GET `/api/v1/auth/me` — 获取当前用户信息

### 愿望模块
- GET/POST `/api/v1/wishes` — 列表/创建（触发AI生成）
- GET/PUT/DELETE `/api/v1/wishes/{id}` — 详情/更新/删除
- POST `/api/v1/wishes/{id}/regenerate` — 重新生成愿景

### 目标模块
- GET/POST `/api/v1/goals` — 列表/创建（触发AI配图+SMART生成）
- GET/PUT/DELETE `/api/v1/goals/{id}` — 详情/更新/删除
- GET `/api/v1/goals/{id}/chain` — 获取完整链路

### 计划模块
- GET/POST `/api/v1/plans` — 列表/创建
- GET/PUT/DELETE `/api/v1/plans/{id}` — 详情/更新/删除
- POST/PUT/DELETE `/api/v1/plans/{id}/steps/{step_id}` — 步骤管理

### 任务模块
- GET/POST `/api/v1/tasks` — 列表（筛选：我的/悬赏/全部）/创建
- GET/PUT/DELETE `/api/v1/tasks/{id}` — 详情/更新/删除
- POST `/api/v1/tasks/{id}/claim` — 认领悬赏任务（行级锁防并发）
- POST `/api/v1/tasks/{id}/submit` — 提交完成（附验证要素）
- GET `/api/v1/tasks/bounty` — 可认领悬赏列表

### 行动模块
- GET/POST `/api/v1/actions` — 列表/创建
- GET/PUT/DELETE `/api/v1/actions/{id}` — 详情/更新/删除
- POST `/api/v1/actions/{id}/complete` — 标记完成
- PUT `/api/v1/actions/{id}/time-log` — 记录时间

### 审核模块
- GET `/api/v1/reviews/pending` — 待审核列表
- POST `/api/v1/reviews/{id}/approve` — 通过（触发积分发放）
- POST `/api/v1/reviews/{id}/reject` — 驳回

### 积分模块
- GET `/api/v1/points/balance` — 积分余额
- GET `/api/v1/points/history` — 积分流水（支持筛选）
- GET `/api/v1/points/leaderboard` — 排行榜

### 日历模块
- GET/POST/PUT/DELETE `/api/v1/calendar/events` — 日历事件CRUD
- GET/POST `/api/v1/calendar/anniversaries` — 纪念日管理

### 食谱模块
- GET/POST/PUT/DELETE `/api/v1/recipes` — 食谱CRUD
- GET `/api/v1/recipes/preferences` — 饮食偏好汇总
- PUT `/api/v1/recipes/preferences/{user_id}` — 更新偏好

### 家庭模块
- POST `/api/v1/families` — 创建家庭
- GET `/api/v1/families/current` — 当前家庭信息
- POST `/api/v1/families/join` — 邀请码加入
- GET/POST `/api/v1/families/members` — 成员列表/添加
- PUT `/api/v1/families/members/{id}/appellation` — 设置称谓
- PUT `/api/v1/families/switch/{family_id}` — 切换家庭视角

### AI生成模块
- GET `/api/v1/ai/generation/{task_id}/status` — 查询生成状态
- POST `/api/v1/ai/regenerate-image` — 重新生成配图
- POST `/api/v1/ai/regenerate-text` — 重新生成文案
- GET `/api/v1/ai/styles` — 可用图片风格列表

## 核心流程设计

### 1. 认证流程
- 微信小程序：wx.login()获取code → 后端换取openid → 查找/创建用户 → 返回JWT
- Web端：手机号 → 发送验证码 → 验证 → 查找/创建用户 → 返回JWT

### 2. AI图文生成流程
- 用户创建内容 → 后端保存基础数据 → 发起Celery异步任务（文案生成+配图生成并行）
- 文案生成：AIServiceAdapter → Redis读取配置 → 调用供应商API → 更新display_text
- 配图生成：AIServiceAdapter → 调用供应商API → 上传OSS → 更新cover_image_url
- 失败处理：尝试fallback模型，最终失败使用默认占位图
- 前端轮询生成状态，completed时刷新卡片

### 3. 目标管理链路状态传播
- 行动完成审核通过 → 更新关联任务进度 → 所有行动完成则任务submitted
- 任务审核通过 → 发放积分 → 更新计划步骤completed → 所有步骤完成则计划completed → 更新目标进度
- 计划过期检查：Celery Beat每小时扫描，标记overdue并通知负责人

### 4. 悬赏任务认领
- 使用数据库行级锁（SELECT FOR UPDATE）防止并发认领
- 认领后设置assignee_id、status=claimed、计算deadline_at

### 5. 重复任务自动生成
- Celery Beat每天凌晨执行，扫描已审核通过的重复任务，生成下一周期实例

### 6. 积分超时惩罚
- Celery Beat每10分钟执行，扫描超时未完成任务，自动扣除惩罚积分并通知

### 7. 审核流程
- 确定审核人：有关联计划→计划负责人；有关联目标→目标负责人；无关联→家庭管理员
- 通过：发放积分 + 更新状态 + 链路传播 + 通知执行人
- 驳回：状态回退in_progress + 通知执行人重新完成

## 前端状态管理（Pinia Stores）

- **UserStore**: currentUser, currentFamily, families; login/phoneLogin/switchFamily/logout
- **WishStore**: wishes列表, 瀑布流分页; createWish触发AI生成, regenerateVision
- **GoalStore**: goals列表, currentGoalChain; createGoal, fetchGoalChain
- **TaskStore**: myTasks, bountyTasks, pendingReviews; claimTask, submitTask
- **PointsStore**: balance, history, leaderboard
- **AIStatusStore**: pendingGenerations Map; pollGenerationStatus, onGenerationComplete

## 通知推送方案

- **微信小程序端**：微信订阅消息（一次性订阅），模板类型：任务提醒/审核通知/积分变动/纪念日提醒/任务认领
- **Web端**：Web Push API + Service Worker；降级方案：页面内通知中心（轮询或SSE）
- **统一通知服务**：NotificationService根据用户渠道选择推送方式，同时写入站内通知表

## 部署架构

- Nginx反向代理（/api/* → FastAPI, /* → H5静态文件）
- FastAPI Worker x2（uvicorn）
- Celery Worker x2 + Beat（定时任务）
- PostgreSQL（主库）
- Redis（缓存+队列）
- 阿里云OSS（图片存储）
- Docker Compose编排所有服务

## 开发计划

- **Phase 1（1-2周）**：基础框架搭建 — FastAPI初始化、数据库模型、JWT认证、uni-app初始化、Docker Compose
- **Phase 2（2-3周）**：核心链路 — 愿望→目标→计划→任务→行动CRUD、链路状态传播、审核流程、积分系统
- **Phase 3（1-2周）**：AI集成 — 后台配置页面、文案/图片生成集成、Celery异步处理、前端状态轮询
- **Phase 4（1-2周）**：辅助模块 — 日历、食谱、家庭成员管理+多家庭视角
- **Phase 5（1周）**：体验优化 — 通知推送、瀑布流布局、深色模式、性能优化
