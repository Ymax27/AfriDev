"""Country endpoints."""

from fastapi import APIRouter

from app.api.dependencies import DbSession
from app.core.schemas import CountryOut
from app.modules.countries import service
from app.modules.countries.schemas import CountryHubOut

router = APIRouter(tags=["countries"])


@router.get("/countries", response_model=list[CountryOut])
async def list_countries(db: DbSession) -> list[CountryOut]:
    return [CountryOut.model_validate(country) for country in await service.list_countries(db)]


@router.get("/countries/{code}", response_model=CountryHubOut)
async def read_country(code: str, db: DbSession) -> CountryHubOut:
    return await service.build_hub(db, code)
