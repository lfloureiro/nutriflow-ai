from fastapi import APIRouter

from backend.app.api.routes_bulk import router as bulk_router
from backend.app.api.routes_dataset_snapshots import router as dataset_snapshots_router
from backend.app.api.routes_feedback import router as feedback_router
from backend.app.api.routes_households import router as households_router
from backend.app.api.routes_ingredients import router as ingredients_router
from backend.app.api.routes_meal_plan import router as meal_plan_router
from backend.app.api.routes_recipes import router as recipes_router
from backend.app.api.routes_shopping_list import router as shopping_list_router

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "NutriFlow AI API a funcionar"}


@router.get("/health")
def health_check():
    return {"status": "ok"}


router.include_router(recipes_router)
router.include_router(ingredients_router)
router.include_router(meal_plan_router)
router.include_router(shopping_list_router)
router.include_router(households_router)
router.include_router(feedback_router)
router.include_router(bulk_router)
router.include_router(dataset_snapshots_router)