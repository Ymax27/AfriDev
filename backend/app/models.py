"""Imports every ORM model so SQLAlchemy metadata and Alembic see all tables."""

from app.core.database import Base
from app.modules.api_directory.models import APIEntry, APIProvider
from app.modules.contributions.models import ContributionRequest
from app.modules.countries.models import Country
from app.modules.field_reports.models import FieldReport, FieldReportConfirmation
from app.modules.knowledge.models import KnowledgeProblem, Solution
from app.modules.messaging.models import Conversation, ConversationMember, Message
from app.modules.missions.models import Mission, MissionSubmission
from app.modules.moderation.models import ContentReport
from app.modules.notifications.models import Notification
from app.modules.projects.models import (
    OwnershipVerification,
    Project,
    ProjectFeedback,
    ProjectLike,
    ProjectPass,
)
from app.modules.reputation.models import ReputationTransaction
from app.modules.users.models import User, UserBlock, UserRole, UserSkill

__all__ = [
    "APIEntry",
    "APIProvider",
    "Base",
    "ContentReport",
    "ContributionRequest",
    "Conversation",
    "ConversationMember",
    "Country",
    "FieldReport",
    "FieldReportConfirmation",
    "KnowledgeProblem",
    "Message",
    "Mission",
    "MissionSubmission",
    "Notification",
    "OwnershipVerification",
    "Project",
    "ProjectFeedback",
    "ProjectLike",
    "ProjectPass",
    "ReputationTransaction",
    "Solution",
    "User",
    "UserBlock",
    "UserRole",
    "UserSkill",
]
