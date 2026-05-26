"""API v1 router aggregating all module routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import actions, admin, ai, auth, calendar, cascade_unlink, families, goals, notifications, plans, points, recipes, reviews, tasks, wishes

api_router = APIRouter()

# Auth module
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Wishes module
api_router.include_router(wishes.router, prefix="/wishes", tags=["wishes"])

# Goals module
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])

# Plans module
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])

# Tasks module
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# Actions module
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])

# Reviews module
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])

# Points module
api_router.include_router(points.router, prefix="/points", tags=["points"])

# Cascade unlink module (downstream links check and unlink)
api_router.include_router(
    cascade_unlink.router, prefix="/entities", tags=["cascade-unlink"]
)

# AI generation module
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

# Admin module
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Calendar module
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])

# Recipes module
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])

# Families module
api_router.include_router(families.router, prefix="/families", tags=["families"])

# Notifications module
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
