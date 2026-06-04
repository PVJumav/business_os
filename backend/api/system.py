from fastapi import APIRouter

from backend.core.system_blueprint import SYSTEM_BLUEPRINT


router = APIRouter(prefix="/system", tags=["System Blueprint"])


@router.get("/blueprint")
def get_system_blueprint():
    return SYSTEM_BLUEPRINT
