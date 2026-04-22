import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = PROJECT_ROOT / "data" / "ml_datasets"
RESULTS_DIR = PROJECT_ROOT / "data" / "ml_results"

DEFAULT_TARGET = "accepted_as_suggested"

BASE_CATEGORICAL_FEATURES = [
    "household_id",
    "meal_type",
    "suggestion_action",
    "suggested_recipe_id",
    "suggested_categoria_alimentar",
    "suggested_proteina_principal",
    "suggested_adequado_refeicao",
]

BASE_NUMERIC_FEATURES = [
    "weekday_index",
    "is_weekend",
    "score",
    "average_rating",
    "ratings_count",
]


def find_latest_dataset() -> Path:
    candidates = sorted(
        DATASET_DIR.glob("*_auto_meal_plan_training_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            "Não foi encontrado nenhum dataset em data/ml_datasets/. "
            "Exporta primeiro o CSV com o script de export."
        )
    return candidates[0]


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset não encontrado: {path}")

    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("O dataset existe, mas não contém linhas.")
    return df


def prepare_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    expected_columns = BASE_CATEGORICAL_FEATURES + BASE_NUMERIC_FEATURES
    missing_columns = [column for column in expected_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "O dataset não contém todas as colunas esperadas para features. "
            f"Em falta: {missing_columns}"
        )

    x = df[expected_columns].copy()

    categorical_features = list(BASE_CATEGORICAL_FEATURES)
    numeric_features: list[str] = []
    dropped_numeric_features: list[str] = []

    for column in categorical_features:
        x[column] = x[column].fillna("unknown").astype(str)

    for column in BASE_NUMERIC_FEATURES:
        x[column] = pd.to_numeric(x[column], errors="coerce")
        if x[column].isna().all():
            dropped_numeric_features.append(column)
        else:
            numeric_features.append(column)

    used_columns = categorical_features + numeric_features
    x = x[used_columns].copy()

    return x, categorical_features, numeric_features, dropped_numeric_features


def prepare_target(df: pd.DataFrame, target_column: str) -> pd.Series:
    if target_column not in df.columns:
        raise ValueError(f"A coluna alvo '{target_column}' não existe no dataset.")

    y = df[target_column].copy()

    if y.dtype == object:
        y = y.fillna("missing").astype(str)

    return y


def make_preprocessor(
    categorical_features: list[str],
    numeric_features: list[str],
) -> ColumnTransformer:
    transformers: list[tuple[str, Pipeline, list[str]]] = []

    if categorical_features:
        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
                (
                    "onehot",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ),
            ]
        )
        transformers.append(("categorical", categorical_pipeline, categorical_features))

    if numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
            ]
        )
        transformers.append(("numeric", numeric_pipeline, numeric_features))

    return ColumnTransformer(transformers=transformers)


def make_models(
    *,
    categorical_features: list[str],
    numeric_features: list[str],
    random_state: int,
) -> dict[str, Pipeline]:
    preprocessor = make_preprocessor(categorical_features, numeric_features)

    return {
        "dummy_most_frequent": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", DummyClassifier(strategy="most_frequent")),
            ]
        ),
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        random_state=random_state,
                        class_weight="balanced",
                    ),
                ),
            ]
        ),
    }


def evaluate_model(
    model_name: str,
    pipeline: Pipeline,
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict[str, Any]:
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    labels = sorted(pd.Series(pd.concat([y_test, pd.Series(predictions)])).astype(str).unique().tolist())

    result = {
        "model_name": model_name,
        "accuracy": accuracy_score(y_test, predictions),
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "precision_weighted": precision_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "recall_weighted": recall_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "f1_weighted": f1_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "confusion_matrix_labels": labels,
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=labels).tolist(),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
    }

    return result


def build_report_path(target: str) -> Path:
    ensure_results_dir()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%SZ")
    return RESULTS_DIR / f"{timestamp}_auto_meal_plan_baseline_{target}.json"


def select_best_model(model_results: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not model_results:
        return None

    return max(
        model_results,
        key=lambda item: (
            item.get("balanced_accuracy", 0),
            item.get("f1_weighted", 0),
            item.get("accuracy", 0),
        ),
    )


def train_auto_meal_plan_baseline(
    *,
    dataset_path: str | None = None,
    target: str = DEFAULT_TARGET,
    test_size: float = 0.3,
    random_state: int = 42,
) -> tuple[Path, dict[str, Any]]:
    resolved_dataset_path = Path(dataset_path) if dataset_path else find_latest_dataset()
    df = load_dataset(resolved_dataset_path)

    target_distribution = (
        df[target].value_counts(dropna=False).to_dict() if target in df.columns else {}
    )

    x, categorical_features, numeric_features, dropped_numeric_features = prepare_features(df)
    y = prepare_target(df, target)

    unique_classes = pd.Series(y).value_counts(dropna=False)

    report: dict[str, Any] = {
        "dataset_path": str(resolved_dataset_path),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_count": int(len(df)),
        "target_column": target,
        "feature_columns_used": categorical_features + numeric_features,
        "categorical_features_used": categorical_features,
        "numeric_features_used": numeric_features,
        "dropped_numeric_features": dropped_numeric_features,
        "target_distribution": {
            str(key): int(value)
            for key, value in target_distribution.items()
        },
        "status": "ok",
        "notes": [],
        "train_size": None,
        "test_size": None,
        "model_results": [],
        "best_model": None,
    }

    if dropped_numeric_features:
        report["notes"].append(
            "Foram removidas features numéricas totalmente vazias: "
            + ", ".join(dropped_numeric_features)
        )

    if len(unique_classes) < 2:
        report["status"] = "not_enough_classes"
        report["notes"].append(
            "O dataset só contém uma classe no target. "
            "Ainda não é possível treinar um modelo supervisionado útil."
        )
        output_path = build_report_path(target)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path, report

    min_class_count = int(unique_classes.min())
    if min_class_count < 2:
        report["status"] = "insufficient_class_support"
        report["notes"].append(
            "Existe pelo menos uma classe com menos de 2 exemplos. "
            "Ainda não há suporte suficiente para split estratificado."
        )
        output_path = build_report_path(target)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path, report

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    report["train_size"] = int(len(x_train))
    report["test_size"] = int(len(x_test))

    models = make_models(
        categorical_features=categorical_features,
        numeric_features=numeric_features,
        random_state=random_state,
    )

    for model_name, pipeline in models.items():
        result = evaluate_model(
            model_name=model_name,
            pipeline=pipeline,
            x_train=x_train,
            x_test=x_test,
            y_train=y_train,
            y_test=y_test,
        )
        report["model_results"].append(result)

    best_model = select_best_model(report["model_results"])
    if best_model:
        report["best_model"] = {
            "model_name": best_model["model_name"],
            "accuracy": best_model["accuracy"],
            "balanced_accuracy": best_model["balanced_accuracy"],
            "f1_weighted": best_model["f1_weighted"],
        }

    output_path = build_report_path(target)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path, report