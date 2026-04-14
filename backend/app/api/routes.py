from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "NutriFlow AI API a funcionar"}


@router.get("/health")
def health_check():
    return {"status": "ok"}