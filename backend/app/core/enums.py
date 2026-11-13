"""Domain enumerations shared by models, schemas and services."""

from enum import StrEnum


class UserRoleType(StrEnum):
    DEVELOPER = "developer"
    PROJECT_CREATOR = "project_creator"
    API_PROVIDER = "api_provider"
    SPONSOR = "sponsor"
    ADMIN = "admin"


class CollaborationMode(StrEnum):
    SHOWCASE = "showcase"
    FEEDBACK = "feedback"
    OPEN_TO_CONTRIBUTORS = "open_to_contributors"


class ContributionDomain(StrEnum):
    CODE = "code"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    TRANSLATION = "translation"


class ContributionStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ReportStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    COMMUNITY_CONFIRMED = "community_confirmed"
    NEEDS_REVALIDATION = "needs_revalidation"
    ARCHIVED = "archived"


class MissionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    COMPLETED = "completed"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ReputationAction(StrEnum):
    ACCEPTED_SOLUTION = "accepted_solution"
    USEFUL_VOTE = "useful_vote"
    FIELD_REPORT_CONFIRMATION = "field_report_confirmation"
    MERGED_CONTRIBUTION = "merged_contribution"
    USEFUL_FEEDBACK = "useful_feedback"
    APPROVED_MISSION = "approved_mission"
    VERIFIED_PROJECT_PUBLICATION = "verified_project_publication"


class ReputationStatus(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    REVERSED = "reversed"


class ConversationType(StrEnum):
    CONTRIBUTION = "contribution"
    COUNTRY = "country"
    MISSION = "mission"


class DeveloperLevel(StrEnum):
    NEWCOMER = "newcomer"
    CONTRIBUTOR = "contributor"
    CONFIRMED = "confirmed"
    EXPERT = "expert"
