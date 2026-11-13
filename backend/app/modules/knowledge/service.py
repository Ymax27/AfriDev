"""Knowledge problems, solutions and accepted-solution workflow."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReputationAction
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.utils import unique_slug
from app.modules.countries.models import Country
from app.modules.field_reports import service as field_report_service
from app.modules.knowledge.models import KnowledgeProblem, Solution
from app.modules.knowledge.schemas import ProblemCreate, SolutionCreate
from app.modules.notifications import service as notification_service
from app.modules.projects.service import resolve_country
from app.modules.reputation import service as reputation_service
from app.modules.users.models import User


async def create_problem(db: AsyncSession, author: User, payload: ProblemCreate) -> KnowledgeProblem:
    country_id = await resolve_country(db, payload.country_code)
    problem = KnowledgeProblem(
        author_id=author.id,
        country_id=country_id or author.country_id,
        api_entry_id=payload.api_entry_id,
        title=payload.title,
        slug=await unique_slug(db, KnowledgeProblem, payload.title),
        description=payload.description,
        category=payload.category,
        technology=payload.technology,
        code_snippet=payload.code_snippet,
        documentation_links=payload.documentation_links,
    )
    db.add(problem)
    await db.commit()
    await db.refresh(problem)
    return problem


async def get_problem(db: AsyncSession, problem_id: UUID) -> KnowledgeProblem:
    problem = await db.get(KnowledgeProblem, problem_id)
    if not problem:
        raise NotFoundError("Problem not found")
    return problem


async def list_problems(
    db: AsyncSession,
    *,
    q: str | None,
    country_code: str | None,
    category: str | None,
    technology: str | None,
    page: int,
    page_size: int,
) -> tuple[list[KnowledgeProblem], int]:
    stmt = select(KnowledgeProblem).order_by(KnowledgeProblem.created_at.desc())
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(KnowledgeProblem.title).like(pattern)
            | func.lower(KnowledgeProblem.description).like(pattern)
        )
    if country_code:
        stmt = stmt.join(Country, KnowledgeProblem.country_id == Country.id).where(
            func.upper(Country.code) == country_code.upper()
        )
    if category:
        stmt = stmt.where(KnowledgeProblem.category == category)
    if technology:
        stmt = stmt.where(
            func.lower(cast(KnowledgeProblem.technology, String)).contains(technology.lower())
        )
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total


async def list_solutions(db: AsyncSession, problem_id: UUID) -> list[Solution]:
    result = await db.execute(
        select(Solution)
        .where(Solution.problem_id == problem_id)
        .order_by(Solution.is_accepted.desc(), Solution.created_at.desc())
    )
    return list(result.scalars().all())


async def solution_stats(db: AsyncSession, problem_ids: list[UUID]) -> dict[UUID, tuple[int, bool]]:
    if not problem_ids:
        return {}
    rows = (
        await db.execute(
            select(
                Solution.problem_id,
                func.count(Solution.id),
                func.max(cast(Solution.is_accepted, String)),
            )
            .where(Solution.problem_id.in_(problem_ids))
            .group_by(Solution.problem_id)
        )
    ).all()
    stats: dict[UUID, tuple[int, bool]] = {}
    for problem_id, count, accepted in rows:
        stats[problem_id] = (int(count), str(accepted).lower() in {"1", "true"})
    return stats


async def add_solution(
    db: AsyncSession, problem: KnowledgeProblem, author: User, payload: SolutionCreate
) -> Solution:
    solution = Solution(
        problem_id=problem.id,
        author_id=author.id,
        explanation=payload.explanation,
        code_snippet=payload.code_snippet,
        implementation_steps=payload.implementation_steps,
        references=payload.references,
    )
    db.add(solution)
    await notification_service.notify(
        db,
        user_id=problem.author_id,
        type="solution_submitted",
        title=f"New solution on '{problem.title}'",
        body=payload.explanation[:180],
        link=f"/knowledge/{problem.id}",
    )
    await db.commit()
    await db.refresh(solution)
    return solution


async def accept_solution(
    db: AsyncSession, problem: KnowledgeProblem, solution: Solution, user: User
) -> Solution:
    if problem.author_id != user.id:
        raise ForbiddenError("Only the problem author can accept a solution")
    if solution.problem_id != problem.id:
        raise ValidationError("This solution does not belong to the problem")
    if solution.author_id == user.id:
        raise ForbiddenError("You cannot accept your own solution")
    if solution.is_accepted:
        return solution

    already_accepted = (
        await db.execute(
            select(Solution.id).where(Solution.problem_id == problem.id, Solution.is_accepted.is_(True))
        )
    ).scalar_one_or_none()
    if already_accepted:
        raise ConflictError("This problem already has an accepted solution")

    solution.is_accepted = True
    solution.accepted_at = datetime.now(UTC)
    await field_report_service.create_from_solution(db, problem, solution)
    await reputation_service.award(
        db,
        user_id=solution.author_id,
        actor_id=user.id,
        action_type=ReputationAction.ACCEPTED_SOLUTION.value,
        reference_type="solution",
        reference_id=str(solution.id),
        is_demo=problem.is_demo,
    )
    await notification_service.notify(
        db,
        user_id=solution.author_id,
        type="solution_accepted",
        title="Your solution was accepted",
        body=f"'{problem.title}' now has an accepted solution and a linked field report.",
        link=f"/knowledge/{problem.id}",
    )
    await db.commit()
    await db.refresh(solution)
    return solution
