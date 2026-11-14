"""Knowledge exchange schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import CountryOut, ORMModel, UserSummary


class ProblemCreate(BaseModel):
    title: str = Field(min_length=8, max_length=200)
    description: str = Field(min_length=30, max_length=8000)
    category: str = Field(min_length=2, max_length=60)
    technology: str | None = Field(default=None, max_length=80)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    api_entry_id: UUID | None = None
    code_snippet: str | None = Field(default=None, max_length=8000)
    documentation_links: list[str] = Field(default_factory=list, max_length=10)


class SolutionCreate(BaseModel):
    explanation: str = Field(min_length=30, max_length=8000)
    code_snippet: str | None = Field(default=None, max_length=8000)
    implementation_steps: str | None = Field(default=None, max_length=4000)
    references: list[str] = Field(default_factory=list, max_length=10)


class SolutionOut(ORMModel):
    id: UUID
    problem_id: UUID
    explanation: str
    code_snippet: str | None = None
    implementation_steps: str | None = None
    references: list[str] = Field(default_factory=list)
    is_accepted: bool
    accepted_at: datetime | None = None
    author: UserSummary
    created_at: datetime
    useful_votes: int = 0
    voted_by_me: bool = False


class ProblemOut(ORMModel):
    id: UUID
    title: str
    slug: str
    description: str
    category: str
    technology: str | None = None
    code_snippet: str | None = None
    documentation_links: list[str] = Field(default_factory=list)
    country: CountryOut | None = None
    api_entry_id: UUID | None = None
    author: UserSummary
    is_demo: bool
    created_at: datetime
    solution_count: int = 0
    has_accepted_solution: bool = False


class ProblemDetailOut(ProblemOut):
    solutions: list[SolutionOut] = Field(default_factory=list)


class ProblemListOut(BaseModel):
    items: list[ProblemOut]
    total: int
    page: int
    page_size: int
