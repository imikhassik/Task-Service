from fastapi import APIRouter, Request


from app.libs.auth import validate_permissions
from app.libs.nestorlog import nlog, nestor

from app.schemas.base.info_schemas import Info

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("", response_model=Info, include_in_schema=False)
@nlog
@validate_permissions
async def get_info(request: Request):
    return Info()
