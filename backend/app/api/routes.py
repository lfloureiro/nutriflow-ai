from fastapi import APIRouter

from backend.app.api.routes_ingredients import router as ingredients_router
from backend.app.api.routes_recipes import router as recipes_router

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "NutriFlow AI API a funcionar"}


@router.get("/health")
def health_check():
    return {"status": "ok"}


router.include_router(recipes_router)
router.include_router(ingredients_router)