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
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = PROJECT_ROOT / "data" / "ml_datasets"
RESULTS_DIR = PROJECT_ROOT / "data" / "ml_results"

DEFAULT_TARGET = "accepted_as_suggested"
DEFAULT_EVALUATION_STRATEGY = "stratified_kfold"
GROUPED_EVALUATION_STRATEGY = "grouped_by_suggested_recipe_id"

CORE_CATEGORICAL_FEATURES = [
    "household_id",
    "meal_type",
    "suggestion_action",
    "suggested_recipe_id",
    "suggested_categoria_alimentar",
    "suggested_proteina_principal",
    "suggested_adequado_refeicao",
]

OPTIONAL_CATEGORICAL_FEATURES = [
    "suggested_family_preference_tier",
    "previous_suggested_categoria_alimentar",
    "previous_suggested_proteina_principal",
    "previous_same_meal_type_categoria_alimentar",
    "previous_same_meal_type_proteina_principal",
]

CORE_NUMERIC_FEATURES = [
    "weekday_index",
    "is_weekend",
    "score",
    "average_rating",
    "ratings_count",
]

OPTIONAL_NUMERIC_FEATURES = [
    "run_slot_index",
    "week_slot_index",
    "days_since_last_auto_plan_same_recipe",
    "weekly_same_category_count_before_slot",
    "weekly_same_protein_count_before_slot",
    "weekly_meal_type_slot_count_before_slot",
    "prior_household_recipe_seen_count",
    "prior_household_recipe_accept_rate",
    "prior_household_recipe_change_rate",
    "prior_household_recipe_delete_rate",
    "suggested_is_family_favorite",
    "reason_family_favorite",
    "reason_good_family_acceptance",
    "reason_low_family_acceptance",
    "reason_specific_meal_type",
    "reason_unrated_neutral",
    "reason_missing_category",
    "reason_missing_protein",
    "reason_recent_last_3_days",
    "reason_recent_last_7_days",
    "reason_recent_last_14_days",
    "reason_recent_last_21_days",
    "reason_already_in_plan",
    "reason_weekly_category_balance",
    "reason_weekly_category_overuse",
    "reason_weekly_meat_rotation",
    "reason_weekly_meat_overuse",
    "reason_same_previous_category",
    "reason_same_previous_protein",
    "reason_recent_category_repeat",
    "reason_three_meats_in_row",
    "reason_recent_meat_protein_repeat",
]

INTERPRETABILITY_TOP_N = 12

FEATURE_SET_WITH_SUGGESTED_RECIPE_ID = {
    "feature_set_key": "with_suggested_recipe_id",
    "feature_set_label": "Com suggested_recipe_id",
    "excluded_features": [],
}

FEATURE_SET_WITHOUT_SUGGESTED_RECIPE_ID = {
    "feature_set_key": "without_suggested_recipe_id",
    "feature_set_label": "Sem suggested_recipe_id",
    "excluded_features": ["suggested_recipe_id"],
}


def to_python_scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def get_ordered_labels(y_true: pd.Series, y_pred: Any) -> list[Any]:
    combined = pd.concat(
        [
            pd.Series(y_true).reset_index(drop=True),
            pd.Series(y_pred).reset_index(drop=True),
        ],
        ignore_index=True,
    ).dropna()

    unique_values = [to_python_scalar(value) for value in pd.unique(combined)]

    try:
        return sorted(unique_values)
    except TypeError:
        return sorted(unique_values, key=lambda value: str(value))


def make_display_labels(labels: list[Any]) -> list[str]:
    return [str(to_python_scalar(label)) for label in labels]


def normalize_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalize_json_value(subvalue) for key, subvalue in value.items()}

    if isinstance(value, list):
        return [normalize_json_value(item) for item in value]

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value

    return value


def safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(pd.Series(values).mean())


def safe_std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(pd.Series(values).std(ddof=0))


def build_ranked_feature_list(
    feature_names: list[str],
    values: list[float],
    *,
    top_n: int = INTERPRETABILITY_TOP_N,
    descending: bool = True,
) -> list[dict[str, Any]]:
    pairs = list(zip(feature_names, values))
    pairs.sort(key=lambda item: item[1], reverse=descending)
    selected = pairs[:top_n]

    return [
        {
            "feature": str(feature_name),
            "value": float(score_value),
        }
        for feature_name, score_value in selected
    ]


def extract_interpretability_from_pipeline(
    pipeline: Pipeline,
) -> dict[str, Any] | None:
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]

    try:
        feature_names = [str(name) for name in preprocessor.get_feature_names_out()]
    except Exception:
        return None

    if isinstance(model, LogisticRegression):
        classes = [str(to_python_scalar(item)) for item in model.classes_]
        coefficients = model.coef_

        if coefficients.shape[0] == 1 and len(classes) == 2:
            coef_values = coefficients[0].tolist()
            return {
                "type": "logistic_regression_coefficients",
                "mode": "binary",
                "positive_class": classes[1],
                "negative_class": classes[0],
                "top_positive_features": build_ranked_feature_list(
                    feature_names,
                    coef_values,
                    descending=True,
                ),
                "top_negative_features": build_ranked_feature_list(
                    feature_names,
                    coef_values,
                    descending=False,
                ),
            }

        class_summaries: list[dict[str, Any]] = []
        for index, class_name in enumerate(classes):
            coef_values = coefficients[index].tolist()
            class_summaries.append(
                {
                    "class_name": class_name,
                    "top_positive_features": build_ranked_feature_list(
                        feature_names,
                        coef_values,
                        descending=True,
                    ),
                    "top_negative_features": build_ranked_feature_list(
                        feature_names,
                        coef_values,
                        descending=False,
                    ),
                }
            )

        return {
            "type": "logistic_regression_coefficients",
            "mode": "multiclass",
            "classes": classes,
            "per_class": class_summaries,
        }

    if isinstance(model, RandomForestClassifier):
        importances = model.feature_importances_.tolist()
        return {
            "type": "random_forest_feature_importances",
            "top_feature_importances": build_ranked_feature_list(
                feature_names,
                importances,
                descending=True,
            ),
        }

    return None


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


def build_feature_set_variants(
    *,
    compare_suggested_recipe_id: bool,
    include_suggested_recipe_id: bool,
) -> list[dict[str, Any]]:
    primary_variant = (
        FEATURE_SET_WITH_SUGGESTED_RECIPE_ID
        if include_suggested_recipe_id
        else FEATURE_SET_WITHOUT_SUGGESTED_RECIPE_ID
    )

    if not compare_suggested_recipe_id:
        return [primary_variant]

    secondary_variant = (
        FEATURE_SET_WITHOUT_SUGGESTED_RECIPE_ID
        if include_suggested_recipe_id
        else FEATURE_SET_WITH_SUGGESTED_RECIPE_ID
    )

    return [primary_variant, secondary_variant]


def prepare_features(
    df: pd.DataFrame,
    *,
    excluded_features: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    excluded_feature_set = set(excluded_features or [])

    required_columns = [
        column
        for column in CORE_CATEGORICAL_FEATURES + CORE_NUMERIC_FEATURES
        if column not in excluded_feature_set
    ]
    missing_required_columns = [column for column in required_columns if column not in df.columns]
    if missing_required_columns:
        raise ValueError(
            "O dataset não contém todas as colunas base esperadas para features. "
            f"Em falta: {missing_required_columns}"
        )

    categorical_features = [
        column for column in CORE_CATEGORICAL_FEATURES if column not in excluded_feature_set
    ]
    numeric_features = [
        column for column in CORE_NUMERIC_FEATURES if column not in excluded_feature_set
    ]

    for column in OPTIONAL_CATEGORICAL_FEATURES:
        if column in df.columns and column not in excluded_feature_set:
            categorical_features.append(column)

    for column in OPTIONAL_NUMERIC_FEATURES:
        if column in df.columns and column not in excluded_feature_set:
            numeric_features.append(column)

    x = df[categorical_features + numeric_features].copy()

    dropped_numeric_features: list[str] = []

    for column in categorical_features:
        x[column] = x[column].fillna("unknown").astype(str)

    filtered_numeric_features: list[str] = []
    for column in numeric_features:
        x[column] = pd.to_numeric(x[column], errors="coerce")
        if x[column].isna().all():
            dropped_numeric_features.append(column)
        else:
            filtered_numeric_features.append(column)

    x = x[categorical_features + filtered_numeric_features].copy()

    return x, categorical_features, filtered_numeric_features, dropped_numeric_features


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
                        solver="liblinear",
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


def build_stratified_kfold_plan(
    *,
    x: pd.DataFrame,
    y: pd.Series,
    random_state: int,
) -> dict[str, Any]:
    min_class_count = int(pd.Series(y).value_counts(dropna=False).min())
    cv_n_splits = min(5, min_class_count)

    if cv_n_splits < 2:
        raise ValueError(
            "Não foi possível determinar pelo menos 2 folds estratificados."
        )

    splitter = StratifiedKFold(
        n_splits=cv_n_splits,
        shuffle=True,
        random_state=random_state,
    )
    fold_indices = list(splitter.split(x, y))
    fold_contexts = [{} for _ in fold_indices]

    return {
        "evaluation_strategy": DEFAULT_EVALUATION_STRATEGY,
        "cv_n_splits": cv_n_splits,
        "fold_indices": fold_indices,
        "fold_contexts": fold_contexts,
        "grouping_feature": None,
        "group_count": None,
    }


def has_at_least_two_classes(y: pd.Series, indices: Any) -> bool:
    return pd.Series(y).iloc[indices].nunique(dropna=False) >= 2


def build_grouped_by_recipe_plan(
    *,
    x: pd.DataFrame,
    df: pd.DataFrame,
    y: pd.Series,
) -> dict[str, Any]:
    if "suggested_recipe_id" not in df.columns:
        raise ValueError(
            "A coluna 'suggested_recipe_id' não existe no dataset, "
            "por isso não é possível usar avaliação agrupada por receita."
        )

    groups = df["suggested_recipe_id"].fillna("missing").astype(str).reset_index(drop=True)
    unique_group_count = int(groups.nunique())

    if unique_group_count < 2:
        raise ValueError(
            "Não existem grupos suficientes em suggested_recipe_id para avaliação agrupada."
        )

    max_splits = min(5, unique_group_count)

    for candidate_splits in range(max_splits, 1, -1):
        splitter = GroupKFold(n_splits=candidate_splits)
        candidate_fold_indices = list(splitter.split(x, y, groups=groups))

        valid_candidate = True
        for train_index, test_index in candidate_fold_indices:
            if not has_at_least_two_classes(y, train_index):
                valid_candidate = False
                break
            if not has_at_least_two_classes(y, test_index):
                valid_candidate = False
                break

        if not valid_candidate:
            continue

        fold_contexts: list[dict[str, Any]] = []
        for train_index, test_index in candidate_fold_indices:
            train_groups = sorted(pd.Series(groups.iloc[train_index]).unique().tolist())
            test_groups = sorted(pd.Series(groups.iloc[test_index]).unique().tolist())

            fold_contexts.append(
                {
                    "train_group_count": len(train_groups),
                    "test_group_count": len(test_groups),
                    "train_groups": [str(item) for item in train_groups],
                    "test_groups": [str(item) for item in test_groups],
                }
            )

        return {
            "evaluation_strategy": GROUPED_EVALUATION_STRATEGY,
            "cv_n_splits": candidate_splits,
            "fold_indices": candidate_fold_indices,
            "fold_contexts": fold_contexts,
            "grouping_feature": "suggested_recipe_id",
            "group_count": unique_group_count,
        }

    raise ValueError(
        "Não foi possível construir folds agrupados por suggested_recipe_id "
        "com pelo menos duas classes nos conjuntos de treino e de teste."
    )


def build_cross_validation_plan(
    *,
    x: pd.DataFrame,
    df: pd.DataFrame,
    y: pd.Series,
    evaluation_strategy: str,
    random_state: int,
) -> dict[str, Any]:
    if evaluation_strategy == DEFAULT_EVALUATION_STRATEGY:
        return build_stratified_kfold_plan(
            x=x,
            y=y,
            random_state=random_state,
        )

    if evaluation_strategy == GROUPED_EVALUATION_STRATEGY:
        return build_grouped_by_recipe_plan(
            x=x,
            df=df,
            y=y,
        )

    raise ValueError(
        f"Estratégia de avaliação desconhecida: {evaluation_strategy}"
    )


def evaluate_model_cross_validated(
    *,
    model_name: str,
    pipeline: Pipeline,
    x: pd.DataFrame,
    y: pd.Series,
    fold_indices: list[tuple[Any, Any]],
    fold_contexts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    fold_results: list[dict[str, Any]] = []
    all_true: list[Any] = []
    all_pred: list[Any] = []

    fold_contexts = fold_contexts or [{} for _ in fold_indices]

    for fold_number, (train_index, test_index) in enumerate(fold_indices, start=1):
        x_train = x.iloc[train_index].reset_index(drop=True)
        x_test = x.iloc[test_index].reset_index(drop=True)
        y_train = y.iloc[train_index].reset_index(drop=True)
        y_test = y.iloc[test_index].reset_index(drop=True)

        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)

        fold_accuracy = float(accuracy_score(y_test, predictions))
        fold_balanced_accuracy = float(balanced_accuracy_score(y_test, predictions))
        fold_precision_weighted = float(
            precision_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        )
        fold_recall_weighted = float(
            recall_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        )
        fold_f1_weighted = float(
            f1_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        )

        fold_result = {
            "fold": fold_number,
            "train_size": int(len(train_index)),
            "test_size": int(len(test_index)),
            "accuracy": fold_accuracy,
            "balanced_accuracy": fold_balanced_accuracy,
            "precision_weighted": fold_precision_weighted,
            "recall_weighted": fold_recall_weighted,
            "f1_weighted": fold_f1_weighted,
        }
        fold_result.update(fold_contexts[fold_number - 1])

        fold_results.append(fold_result)

        all_true.extend([to_python_scalar(value) for value in y_test.tolist()])
        all_pred.extend([to_python_scalar(value) for value in predictions.tolist()])

    aggregated_true = pd.Series(all_true)
    aggregated_pred = pd.Series(all_pred)

    actual_labels = get_ordered_labels(aggregated_true, aggregated_pred)
    display_labels = make_display_labels(actual_labels)

    accuracy_values = [item["accuracy"] for item in fold_results]
    balanced_accuracy_values = [item["balanced_accuracy"] for item in fold_results]
    precision_values = [item["precision_weighted"] for item in fold_results]
    recall_values = [item["recall_weighted"] for item in fold_results]
    f1_values = [item["f1_weighted"] for item in fold_results]

    return {
        "model_name": model_name,
        "fold_count": len(fold_results),
        "fold_results": fold_results,
        "accuracy": safe_mean(accuracy_values),
        "accuracy_std": safe_std(accuracy_values),
        "balanced_accuracy": safe_mean(balanced_accuracy_values),
        "balanced_accuracy_std": safe_std(balanced_accuracy_values),
        "precision_weighted": safe_mean(precision_values),
        "precision_weighted_std": safe_std(precision_values),
        "recall_weighted": safe_mean(recall_values),
        "recall_weighted_std": safe_std(recall_values),
        "f1_weighted": safe_mean(f1_values),
        "f1_weighted_std": safe_std(f1_values),
        "confusion_matrix_labels": display_labels,
        "confusion_matrix": confusion_matrix(
            aggregated_true,
            aggregated_pred,
            labels=actual_labels,
        ).tolist(),
        "classification_report": normalize_json_value(
            classification_report(
                aggregated_true,
                aggregated_pred,
                labels=actual_labels,
                output_dict=True,
                zero_division=0,
            )
        ),
        "interpretability": None,
    }


def build_report_path(target: str, evaluation_strategy: str) -> Path:
    ensure_results_dir()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%SZ")
    return RESULTS_DIR / f"{timestamp}_auto_meal_plan_baseline_{target}_{evaluation_strategy}.json"


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


def build_feature_set_report(
    *,
    df: pd.DataFrame,
    y: pd.Series,
    feature_set_variant: dict[str, Any],
    fold_indices: list[tuple[Any, Any]],
    fold_contexts: list[dict[str, Any]],
    random_state: int,
) -> dict[str, Any]:
    x, categorical_features, numeric_features, dropped_numeric_features = prepare_features(
        df,
        excluded_features=feature_set_variant["excluded_features"],
    )

    feature_set_report: dict[str, Any] = {
        "feature_set_key": feature_set_variant["feature_set_key"],
        "feature_set_label": feature_set_variant["feature_set_label"],
        "excluded_features": list(feature_set_variant["excluded_features"]),
        "feature_columns_used": categorical_features + numeric_features,
        "categorical_features_used": categorical_features,
        "numeric_features_used": numeric_features,
        "dropped_numeric_features": dropped_numeric_features,
        "model_results": [],
        "best_model": None,
    }

    models = make_models(
        categorical_features=categorical_features,
        numeric_features=numeric_features,
        random_state=random_state,
    )

    for model_name, pipeline in models.items():
        result = evaluate_model_cross_validated(
            model_name=model_name,
            pipeline=pipeline,
            x=x,
            y=y,
            fold_indices=fold_indices,
            fold_contexts=fold_contexts,
        )

        fitted_pipeline = make_models(
            categorical_features=categorical_features,
            numeric_features=numeric_features,
            random_state=random_state,
        )[model_name]
        fitted_pipeline.fit(x, y)
        result["interpretability"] = extract_interpretability_from_pipeline(fitted_pipeline)

        feature_set_report["model_results"].append(result)

    best_model = select_best_model(feature_set_report["model_results"])
    if best_model:
        feature_set_report["best_model"] = {
            "model_name": best_model["model_name"],
            "accuracy": best_model["accuracy"],
            "accuracy_std": best_model["accuracy_std"],
            "balanced_accuracy": best_model["balanced_accuracy"],
            "balanced_accuracy_std": best_model["balanced_accuracy_std"],
            "f1_weighted": best_model["f1_weighted"],
            "f1_weighted_std": best_model["f1_weighted_std"],
            "confusion_matrix_labels": best_model["confusion_matrix_labels"],
            "confusion_matrix": best_model["confusion_matrix"],
            "interpretability": best_model["interpretability"],
        }

    return feature_set_report


def apply_primary_feature_set_to_top_level_report(
    report: dict[str, Any],
    primary_feature_set_report: dict[str, Any],
) -> None:
    report["feature_set_key_primary"] = primary_feature_set_report["feature_set_key"]
    report["feature_set_label_primary"] = primary_feature_set_report["feature_set_label"]
    report["excluded_features_primary"] = primary_feature_set_report["excluded_features"]
    report["feature_columns_used"] = primary_feature_set_report["feature_columns_used"]
    report["categorical_features_used"] = primary_feature_set_report["categorical_features_used"]
    report["numeric_features_used"] = primary_feature_set_report["numeric_features_used"]
    report["dropped_numeric_features"] = primary_feature_set_report[
        "dropped_numeric_features"
    ]
    report["model_results"] = primary_feature_set_report["model_results"]
    report["best_model"] = primary_feature_set_report["best_model"]


def build_comparison_summary(
    feature_set_reports: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if len(feature_set_reports) < 2:
        return None

    variants: list[dict[str, Any]] = []
    for feature_set_report in feature_set_reports:
        best_model = feature_set_report.get("best_model")
        if best_model is None:
            continue

        variants.append(
            {
                "feature_set_key": feature_set_report["feature_set_key"],
                "feature_set_label": feature_set_report["feature_set_label"],
                "excluded_features": feature_set_report["excluded_features"],
                "feature_count": len(feature_set_report["feature_columns_used"]),
                "best_model_name": best_model["model_name"],
                "best_balanced_accuracy": best_model["balanced_accuracy"],
                "best_balanced_accuracy_std": best_model["balanced_accuracy_std"],
                "best_f1_weighted": best_model["f1_weighted"],
                "best_f1_weighted_std": best_model["f1_weighted_std"],
            }
        )

    if not variants:
        return None

    best_variant = max(
        variants,
        key=lambda item: (
            item["best_balanced_accuracy"],
            item["best_f1_weighted"],
        ),
    )

    return {
        "compared_feature": "suggested_recipe_id",
        "variants": variants,
        "best_variant": best_variant,
    }


def train_auto_meal_plan_baseline(
    *,
    dataset_path: str | None = None,
    target: str = DEFAULT_TARGET,
    test_size: float = 0.3,
    random_state: int = 42,
    include_suggested_recipe_id: bool = True,
    compare_suggested_recipe_id: bool = False,
    evaluation_strategy: str = DEFAULT_EVALUATION_STRATEGY,
) -> tuple[Path, dict[str, Any]]:
    del test_size

    resolved_dataset_path = Path(dataset_path) if dataset_path else find_latest_dataset()
    df = load_dataset(resolved_dataset_path)

    target_distribution = (
        df[target].value_counts(dropna=False).to_dict() if target in df.columns else {}
    )

    y = prepare_target(df, target)
    feature_set_variants = build_feature_set_variants(
        compare_suggested_recipe_id=compare_suggested_recipe_id,
        include_suggested_recipe_id=include_suggested_recipe_id,
    )

    primary_feature_set_report = {
        "feature_set_key": feature_set_variants[0]["feature_set_key"],
        "feature_set_label": feature_set_variants[0]["feature_set_label"],
        "excluded_features": list(feature_set_variants[0]["excluded_features"]),
        "feature_columns_used": [],
        "categorical_features_used": [],
        "numeric_features_used": [],
        "dropped_numeric_features": [],
        "model_results": [],
        "best_model": None,
    }

    primary_x, primary_categorical_features, primary_numeric_features, primary_dropped_numeric_features = (
        prepare_features(
            df,
            excluded_features=feature_set_variants[0]["excluded_features"],
        )
    )

    unique_classes = pd.Series(y).value_counts(dropna=False)

    report: dict[str, Any] = {
        "dataset_path": str(resolved_dataset_path),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_count": int(len(df)),
        "target_column": target,
        "evaluation_strategy": evaluation_strategy,
        "grouping_feature": None,
        "group_count": None,
        "comparison_requested": compare_suggested_recipe_id,
        "comparison_target_feature": "suggested_recipe_id",
        "feature_set_variants_requested": [
            variant["feature_set_key"] for variant in feature_set_variants
        ],
        "status": "ok",
        "notes": [
            "As métricas representam média e desvio padrão por fold de validação cruzada.",
            "A interpretabilidade é calculada ajustando o modelo em todo o dataset apenas para inspeção exploratória.",
        ],
        "target_distribution": {
            str(key): int(value)
            for key, value in target_distribution.items()
        },
        "train_size": None,
        "test_size": None,
        "cv_n_splits": None,
        "feature_set_reports": [],
        "comparison_summary": None,
        "feature_set_key_primary": primary_feature_set_report["feature_set_key"],
        "feature_set_label_primary": primary_feature_set_report["feature_set_label"],
        "excluded_features_primary": primary_feature_set_report["excluded_features"],
        "feature_columns_used": primary_categorical_features + primary_numeric_features,
        "categorical_features_used": primary_categorical_features,
        "numeric_features_used": primary_numeric_features,
        "dropped_numeric_features": primary_dropped_numeric_features,
        "model_results": [],
        "best_model": None,
    }

    if report["dropped_numeric_features"]:
        report["notes"].append(
            "Foram removidas features numéricas totalmente vazias no feature set primário: "
            + ", ".join(report["dropped_numeric_features"])
        )

    if len(unique_classes) < 2:
        report["status"] = "not_enough_classes"
        report["notes"].append(
            "O dataset só contém uma classe no target. "
            "Ainda não é possível treinar um modelo supervisionado útil."
        )
        output_path = build_report_path(target, evaluation_strategy)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path, report

    min_class_count = int(unique_classes.min())
    if min_class_count < 2:
        report["status"] = "insufficient_class_support"
        report["notes"].append(
            "Existe pelo menos uma classe com menos de 2 exemplos. "
            "Ainda não há suporte suficiente para validação cruzada."
        )
        output_path = build_report_path(target, evaluation_strategy)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path, report

    try:
        cv_plan = build_cross_validation_plan(
            x=primary_x,
            df=df,
            y=y,
            evaluation_strategy=evaluation_strategy,
            random_state=random_state,
        )
    except ValueError as exc:
        report["status"] = "insufficient_evaluation_support"
        report["notes"].append(str(exc))
        output_path = build_report_path(target, evaluation_strategy)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path, report

    report["evaluation_strategy"] = cv_plan["evaluation_strategy"]
    report["cv_n_splits"] = cv_plan["cv_n_splits"]
    report["train_size"] = int(len(cv_plan["fold_indices"][0][0]))
    report["test_size"] = int(len(cv_plan["fold_indices"][0][1]))
    report["grouping_feature"] = cv_plan["grouping_feature"]
    report["group_count"] = cv_plan["group_count"]

    if report["evaluation_strategy"] == GROUPED_EVALUATION_STRATEGY:
        report["notes"].append(
            "Nesta avaliação, os folds são agrupados por suggested_recipe_id para testar generalização para receitas não vistas no treino."
        )
        report["notes"].append(
            "Os folds agrupados foram escolhidos de modo a garantir pelo menos duas classes nos conjuntos de treino e de teste."
        )

    for feature_set_variant in feature_set_variants:
        feature_set_report = build_feature_set_report(
            df=df,
            y=y,
            feature_set_variant=feature_set_variant,
            fold_indices=cv_plan["fold_indices"],
            fold_contexts=cv_plan["fold_contexts"],
            random_state=random_state,
        )
        report["feature_set_reports"].append(feature_set_report)

        if feature_set_report["dropped_numeric_features"]:
            report["notes"].append(
                "Foram removidas features numéricas totalmente vazias em "
                f"{feature_set_report['feature_set_label']}: "
                + ", ".join(feature_set_report["dropped_numeric_features"])
            )

        if (
            feature_set_report["feature_set_key"]
            == report["feature_set_key_primary"]
        ):
            apply_primary_feature_set_to_top_level_report(report, feature_set_report)

    report["comparison_summary"] = build_comparison_summary(report["feature_set_reports"])

    output_path = build_report_path(target, evaluation_strategy)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path, report