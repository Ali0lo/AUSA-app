from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.export import router as export_router
from app.api.v1.routes import router as routes_router
from app.api.v1.catalogue import router as catalogue_router
from app.api.v1.azerbaijan import router as azerbaijan_router
from app.api.v1.finance import router as finance_router
from app.api.v1.scholarships import router as scholarships_router
from app.api.v1.dim_calculator import router as dim_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(admin_router)
api_router.include_router(export_router)
api_router.include_router(applications_router)
api_router.include_router(routes_router)
api_router.include_router(catalogue_router)
api_router.include_router(azerbaijan_router)
api_router.include_router(finance_router)
api_router.include_router(scholarships_router)
api_router.include_router(dim_router)

