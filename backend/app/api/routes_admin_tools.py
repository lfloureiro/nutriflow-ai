from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.admin_test_reset import reset_meal_plan_ml_state
from backend.app.services.auto_meal_plan_baseline_training import (
    DEFAULT_TARGET,
    train_auto_meal_plan_baseline,
)
from backend.app.services.auto_meal_plan_model_publishing import (
    DEFAULT_PUBLISH_EVALUATION_STRATEGY,
    DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID,
    DEFAULT_PUBLISH_TARGET,
    publish_auto_meal_plan_model,
)
from backend.app.services.auto_meal_plan_model_runtime import (
    load_published_auto_meal_plan_model_artifact,
    summarize_published_auto_meal_plan_artifact,
)
from backend.app.services.auto_meal_plan_training_dataset import (
    export_auto_plan_training_dataset,
)

router = APIRouter(prefix="/admin-tools", tags=["admin-tools"])


@router.post("/ml/export-auto-plan-dataset")
def export_auto_plan_dataset(
    household_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        path, row_count = export_auto_plan_training_dataset(
            db,
            household_id=household_id,
            output_path=None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Dataset exportado com sucesso.",
        "dataset_path": str(path),
        "row_count": row_count,
        "household_id": household_id,
    }


@router.post("/ml/train-auto-plan-baseline")
def train_auto_plan_baseline(
    dataset_path: str | None = Query(default=None),
    target: str = Query(default=DEFAULT_TARGET),
    test_size: float = Query(default=0.3),
    random_state: int = Query(default=42),
):
    try:
        report_path, report = train_auto_meal_plan_baseline(
            dataset_path=dataset_path,
            target=target,
            test_size=test_size,
            random_state=random_state,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Treino baseline processado com sucesso.",
        "report_path": str(report_path),
        "status": report["status"],
        "row_count": report["row_count"],
        "target_column": report["target_column"],
        "train_size": report["train_size"],
        "test_size": report["test_size"],
        "notes": report["notes"],
        "best_model": report["best_model"],
    }


@router.post("/ml/publish-auto-plan-model")
def publish_auto_plan_model(
    dataset_path: str | None = Query(default=None),
    target: str = Query(default=DEFAULT_PUBLISH_TARGET),
    test_size: float = Query(default=0.3),
    random_state: int = Query(default=42),
    include_suggested_recipe_id: bool = Query(default=DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID),
    evaluation_strategy: str = Query(default=DEFAULT_PUBLISH_EVALUATION_STRATEGY),
):
    try:
        model_path, report_path, metadata = publish_auto_meal_plan_model(
            dataset_path=dataset_path,
            target=target,
            test_size=test_size,
            random_state=random_state,
            include_suggested_recipe_id=include_suggested_recipe_id,
            evaluation_strategy=evaluation_strategy,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Modelo de auto-planeamento publicado com sucesso.",
        "model_path": str(model_path),
        "report_path": str(report_path),
        **metadata,
    }


@router.get("/ml/active-auto-plan-model")
def get_active_auto_plan_model():
    artifact = load_published_auto_meal_plan_model_artifact()
    metadata = summarize_published_auto_meal_plan_artifact(artifact)

    return {
        "active": metadata is not None,
        "model": metadata,
    }


@router.post("/testing/reset-meal-plan-ml-state")
def reset_testing_meal_plan_ml_state(
    db: Session = Depends(get_db),
):
    try:
        result = reset_meal_plan_ml_state(db)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Plano, eventos e artefactos ML limpos com sucesso.",
        **result,
    }
