"""Knowledge exchange endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.core.exceptions import NotFoundError
from app.modules.knowledge import service
from app.modules.knowledge.models import Solution
from app.modules.knowledge.schemas import (
    ProblemCreate,
    ProblemDetailOut,
    ProblemListOut,
    ProblemOut,
    SolutionCreate,
    SolutionOut,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=ProblemListOut)
async def list_problems(
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    q: str | None = Query(default=None, max_length=100),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    category: str | None = Query(default=None, max_length=60),
    technology: str | None = Query(default=None, max_length=80),
) -> ProblemListOut:
    problems, total = await service.list_problems(
        db,
        q=q,
        country_code=country,
        category=category,
        technology=technology,
        page=paging.page,
        page_size=paging.page_size,
    )
    stats = await service.solution_stats(db, [problem.id for problem in problems])
    items = []
    for problem in problems:
        count, accepted = stats.get(problem.id, (0, False))
        items.append(
            ProblemOut.model_validate(problem).model_copy(
                update={"solution_count": count, "has_accepted_solution": accepted}
            )
        )
    return ProblemListOut(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.post("", response_model=ProblemOut, status_code=201)
async def create_problem(payload: ProblemCreate, user: CurrentUser, db: DbSession) -> ProblemOut:
    problem = await service.create_problem(db, user, payload)
    return ProblemOut.model_validate(problem)


@router.get("/{problem_id}", response_model=ProblemDetailOut)
async def read_problem(problem_id: UUID, db: DbSession) -> ProblemDetailOut:
    problem = await service.get_problem(db, problem_id)
    solutions = await service.list_solutions(db, problem_id)
    base = ProblemOut.model_validate(problem)
    return ProblemDetailOut(
        **base.model_dump(),
        solution_count=len(solutions),
        has_accepted_solution=any(solution.is_accepted for solution in solutions),
        solutions=[SolutionOut.model_validate(solution) for solution in solutions],
    )


@router.post("/{problem_id}/solutions", response_model=SolutionOut, status_code=201)
async def add_solution(
    problem_id: UUID, payload: SolutionCreate, user: CurrentUser, db: DbSession
) -> SolutionOut:
    problem = await service.get_problem(db, problem_id)
    return SolutionOut.model_validate(await service.add_solution(db, problem, user, payload))


@router.post("/{problem_id}/solutions/{solution_id}/accept", response_model=SolutionOut)
async def accept_solution(
    problem_id: UUID, solution_id: UUID, user: CurrentUser, db: DbSession
) -> SolutionOut:
    problem = await service.get_problem(db, problem_id)
    solution = await db.get(Solution, solution_id)
    if solution is None or solution.problem_id != problem_id:
        raise NotFoundError("Solution not found")
    return SolutionOut.model_validate(await service.accept_solution(db, problem, solution, user))
