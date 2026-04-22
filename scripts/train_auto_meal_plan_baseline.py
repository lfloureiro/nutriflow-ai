import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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

DATASET_DIR = PROJECT_ROOT / "data" / "ml_datasets"
RESULTS_DIR = PROJECT_ROOT / "data" / "ml_results"

DEFAULT_TARGET = "accepted_as_suggested"

CATEGORICAL_FEATURES = [
    "household_id",
    "meal_type",
    "suggestion_action",
    "suggested_recipe_id",
    "suggested_categoria_alimentar",
    "suggested_proteina_principal",
    "suggested_adequado_refeicao",
]

NUMERIC_FEATURES = [
    "weekday_index",
    "is_weekend",
    "score",
    "average_rating",
    "ratings_count",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def parse_args():
    parser = argparse.ArgumentParser(
        description="Treina baselines de ML a partir do dataset exportado do auto-planeamento."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Caminho explícito para o CSV. Se não for dado, usa o mais recente em data/ml_datasets/.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=DEFAULT_TARGET,
        help=f"Coluna alvo a usar. Por defeito: {DEFAULT_TARGET}",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.3,
        help="Percentagem do conjunto de teste. Por defeito: 0.3",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Seed para reprodutibilidade. Por defeito: 42",
    )
    return parser.parse_args()


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


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [column for column in FEATURE_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(
            f"O dataset não contém todas as colunas esperadas para features. "
            f"Em falta: {missing_columns}"
        )

    x = df[FEATURE_COLUMNS].copy()

    for column in CATEGORICAL_FEATURES:
        x[column] = x[column].fillna("unknown").astype(str)

    for column in NUMERIC_FEATURES:
        x[column] = pd.to_numeric(x[column], errors="coerce")

    return x


def prepare_target(df: pd.DataFrame, target_column: str) -> pd.Series:
    if target_column not in df.columns:
        raise ValueError(f"A coluna alvo '{target_column}' não existe no dataset.")

    y = df[target_column].copy()

    if y.dtype == object:
        y = y.fillna("missing").astype(str)

    return y


def make_preprocessor() -> ColumnTransformer:
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ]
    )


def make_models(random_state: int) -> dict[str, Pipeline]:
    preprocessor = make_preprocessor()

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

    labels = sorted(pd.Series(y_test).astype(str).unique().tolist())

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


def main():
    args = parse_args()

    dataset_path = Path(args.dataset) if args.dataset else find_latest_dataset()
    df = load_dataset(dataset_path)

    target_distribution = df[args.target].value_counts(dropna=False).to_dict() if args.target in df.columns else {}
    print(f"Dataset: {dataset_path}")
    print(f"Número de linhas: {len(df)}")
    print(f"Target: {args.target}")
    if target_distribution:
        print(f"Distribuição do target: {target_distribution}")

    x = prepare_features(df)
    y = prepare_target(df, args.target)

    unique_classes = pd.Series(y).value_counts(dropna=False)
    report: dict[str, Any] = {
        "dataset_path": str(dataset_path),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_count": int(len(df)),
        "target_column": args.target,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "target_distribution": {
            str(key): int(value)
            for key, value in unique_classes.to_dict().items()
        },
        "status": "ok",
        "notes": [],
        "train_size": None,
        "test_size": None,
        "model_results": [],
    }

    if len(unique_classes) < 2:
        report["status"] = "not_enough_classes"
        report["notes"].append(
            "O dataset só contém uma classe no target. "
            "Ainda não é possível treinar um modelo supervisionado útil."
        )
        output_path = build_report_path(args.target)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Treino ignorado: só existe uma classe no target.")
        print(f"Relatório gravado em: {output_path}")
        return

    min_class_count = int(unique_classes.min())
    if min_class_count < 2:
        report["status"] = "insufficient_class_support"
        report["notes"].append(
            "Existe pelo menos uma classe com menos de 2 exemplos. "
            "Ainda não há suporte suficiente para split estratificado."
        )
        output_path = build_report_path(args.target)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Treino ignorado: pelo menos uma classe tem menos de 2 exemplos.")
        print(f"Relatório gravado em: {output_path}")
        return

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    report["train_size"] = int(len(x_train))
    report["test_size"] = int(len(x_test))

    models = make_models(args.random_state)

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

        print(
            f"[{model_name}] "
            f"accuracy={result['accuracy']:.4f} "
            f"balanced_accuracy={result['balanced_accuracy']:.4f} "
            f"f1_weighted={result['f1_weighted']:.4f}"
        )

    output_path = build_report_path(args.target)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Relatório gravado em: {output_path}")


if __name__ == "__main__":
    main()