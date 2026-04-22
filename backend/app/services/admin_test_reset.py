from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.models.meal_feedback import MealFeedback
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.shopping_list_item_state import ShoppingListItemState

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = PROJECT_ROOT / "data" / "ml_datasets"
RESULTS_DIR = PROJECT_ROOT / "data" / "ml_results"


def delete_files_in_directory(path: Path) -> int:
    if not path.exists():
        return 0

    deleted_count = 0
    for child in path.iterdir():
        if child.is_file():
            child.unlink()
            deleted_count += 1

    return deleted_count


def reset_meal_plan_ml_state(db: Session) -> dict[str, int]:
    deleted_meal_feedback_count = db.query(MealFeedback).delete(synchronize_session=False)
    deleted_auto_event_count = db.query(AutoMealPlanEvent).delete(synchronize_session=False)
    deleted_shopping_state_count = db.query(ShoppingListItemState).delete(synchronize_session=False)
    deleted_meal_plan_count = db.query(MealPlanItem).delete(synchronize_session=False)

    db.commit()

    deleted_dataset_file_count = delete_files_in_directory(DATASET_DIR)
    deleted_result_file_count = delete_files_in_directory(RESULTS_DIR)

    return {
        "deleted_meal_feedback_count": int(deleted_meal_feedback_count or 0),
        "deleted_auto_event_count": int(deleted_auto_event_count or 0),
        "deleted_shopping_state_count": int(deleted_shopping_state_count or 0),
        "deleted_meal_plan_count": int(deleted_meal_plan_count or 0),
        "deleted_dataset_file_count": int(deleted_dataset_file_count),
        "deleted_result_file_count": int(deleted_result_file_count),
    }