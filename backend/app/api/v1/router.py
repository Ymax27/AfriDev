"""Version 1 API router."""

from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.api_directory.router import router as api_directory_router
from app.modules.auth.router import router as auth_router
from app.modules.contributions.router import router as contributions_router
from app.modules.countries.router import router as countries_router
from app.modules.field_reports.router import router as field_reports_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.leaderboard.router import router as leaderboard_router
from app.modules.messaging.router import router as messaging_router
from app.modules.missions.router import router as missions_router
from app.modules.moderation.router import router as moderation_router
from app.modules.notifications.router import router as notifications_router
from app.modules.projects.router import router as projects_router
from app.modules.reputation.router import router as reputation_router
from app.modules.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(countries_router)
api_router.include_router(projects_router)
api_router.include_router(contributions_router)
api_router.include_router(knowledge_router)
api_router.include_router(field_reports_router)
api_router.include_router(reputation_router)
api_router.include_router(leaderboard_router)
api_router.include_router(missions_router)
api_router.include_router(api_directory_router)
api_router.include_router(messaging_router)
api_router.include_router(notifications_router)
api_router.include_router(moderation_router)
api_router.include_router(admin_router)
