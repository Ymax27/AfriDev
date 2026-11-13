"""Field report lifecycle, confirmations and 90-day revalidation."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import ReportStatus, ReputationAction
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.countries.models import Country
from app.modules.field_reports.models import FieldReport, FieldReportConfirmation
from app.modules.field_reports.schemas import FieldReportUpdate
from app.modules.knowledge.models import KnowledgeProblem, Solution
from app.modules.notifications import service as notification_service
from app.modules.reputation import service as reputation_service
from app.modules.users.models import User


def effective_status(report: FieldReport) -> str:
    """Reports untouched for the revalidation window are flagged, never deleted."""
    if report.status == ReportStatus.ARCHIVED.value:
        return report.status
    reference = report.last_validated_at or report.created_at
    if reference and reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    if reference and datetime.now(UTC) - reference > timedelta(
        days=settings.field_report_revalidation_days
    ):
        return ReportStatus.NEEDS_REVALIDATION.value
    return report.status


async def create_from_solution(
    db: AsyncSession, problem: KnowledgeProblem, solution: Solution
) -> FieldReport:
    report = FieldReport(
        problem_id=problem.id,
        solution_id=solution.id,
        author_id=solution.author_id,
        country_id=problem.country_id,
        api_entry_id=problem.api_entry_id,
        title=problem.title,
        problem_summary=problem.description[:4000],
        solution_summary=solution.explanation[:4000],
        status=ReportStatus.PUBLISHED.value,
        confirmation_count=0,
        is_demo=problem.is_demo,
    )
    db.add(report)
    await db.flush()
    return report


async def get_report(db: AsyncSession, report_id: UUID) -> FieldReport:
    report = await db.get(FieldReport, report_id)
    if not report:
        raise NotFoundError("Field report not found")
    return report


async def list_reports(
    db: AsyncSession,
    *,
    q: str | None,
    country_code: str | None,
    api_entry_id: UUID | None,
    status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[FieldReport], int]:
    stmt = select(FieldReport).order_by(FieldReport.created_at.desc())
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(FieldReport.title).like(pattern)
            | func.lower(FieldReport.problem_summary).like(pattern)
            | func.lower(FieldReport.solution_summary).like(pattern)
        )
    if country_code:
        stmt = stmt.join(Country, FieldReport.country_id == Country.id).where(
            func.upper(Country.code) == country_code.upper()
        )
    if api_entry_id:
        stmt = stmt.where(FieldReport.api_entry_id == api_entry_id)
    if status:
        stmt = stmt.where(FieldReport.status == status)
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total


async def update_report(
    db: AsyncSession, report: FieldReport, user: User, payload: FieldReportUpdate
) -> FieldReport:
    if report.author_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the report author can enrich this field report")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    await db.commit()
    await db.refresh(report)
    return report


async def confirm_report(
    db: AsyncSession, report: FieldReport, user: User, comment: str | None
) -> FieldReport:
    if report.author_id == user.id:
        raise ForbiddenError("You cannot confirm your own field report")
    if report.country_id and user.country_id != report.country_id and not user.is_admin:
        raise ForbiddenError("Only developers from the report's country can confirm it")

    existing = (
        await db.execute(
            select(FieldReportConfirmation).where(
                FieldReportConfirmation.report_id == report.id,
                FieldReportConfirmation.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("You already confirmed this field report")

    db.add(
        FieldReportConfirmation(
            report_id=report.id, user_id=user.id, country_id=user.country_id, comment=comment
        )
    )
    report.confirmation_count = report.confirmation_count + 1
    report.last_validated_at = datetime.now(UTC)
    if report.confirmation_count >= 2:
        report.status = ReportStatus.COMMUNITY_CONFIRMED.value
    else:
        report.status = ReportStatus.PUBLISHED.value

    await reputation_service.award(
        db,
        user_id=user.id,
        action_type=ReputationAction.FIELD_REPORT_CONFIRMATION.value,
        reference_type="field_report",
        reference_id=str(report.id),
        is_demo=report.is_demo,
    )
    await notification_service.notify(
        db,
        user_id=report.author_id,
        type="field_report_confirmed",
        title="Your field report was confirmed",
        body=f"{user.username} confirmed '{report.title}'",
        link=f"/field-reports/{report.id}",
    )
    await db.commit()
    await db.refresh(report)
    return report


async def list_confirmations(db: AsyncSession, report_id: UUID) -> list[FieldReportConfirmation]:
    result = await db.execute(
        select(FieldReportConfirmation)
        .where(FieldReportConfirmation.report_id == report_id)
        .order_by(FieldReportConfirmation.created_at.desc())
    )
    return list(result.scalars().all())


async def flag_stale_reports(db: AsyncSession) -> int:
    """Mark reports whose last validation is older than the revalidation window."""
    threshold = datetime.now(UTC) - timedelta(days=settings.field_report_revalidation_days)
    result = await db.execute(
        select(FieldReport).where(
            FieldReport.status.in_(
                [ReportStatus.PUBLISHED.value, ReportStatus.COMMUNITY_CONFIRMED.value]
            ),
            func.coalesce(FieldReport.last_validated_at, FieldReport.created_at) < threshold,
        )
    )
    reports = result.scalars().all()
    for report in reports:
        report.status = ReportStatus.NEEDS_REVALIDATION.value
    await db.commit()
    return len(reports)
