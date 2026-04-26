from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Sequence

from backend.app.models.recipe_preference import RecipePreference

GROUP_SCORE_OUTLIER_PENALTY = 0.15
GROUP_SCORE_MIN_RATINGS_FOR_OUTLIER_SOFTENING = 4


@dataclass(frozen=True)
class RecipePreferenceScoreSummary:
    ratings_count: int
    average_rating: float
    effective_rating: float
    median_rating: float
    lowest_rating: float
    highest_rating: float
    base_rating: float
    disagreement_penalty: float
    disagreement_spread: float
    conflict_flag: bool


def _round_rating(value: float) -> float:
    return round(float(value), 2)


def build_recipe_preference_score_summary_from_ratings(
    ratings: Sequence[int | float],
) -> RecipePreferenceScoreSummary:
    normalized_ratings = sorted(
        [float(rating) for rating in ratings],
        reverse=True,
    )

    if not normalized_ratings:
        return RecipePreferenceScoreSummary(
            ratings_count=0,
            average_rating=0.0,
            effective_rating=0.0,
            median_rating=0.0,
            lowest_rating=0.0,
            highest_rating=0.0,
            base_rating=0.0,
            disagreement_penalty=0.0,
            disagreement_spread=0.0,
            conflict_flag=False,
        )

    ratings_count = len(normalized_ratings)
    average_rating = sum(normalized_ratings) / ratings_count
    median_rating = float(median(normalized_ratings))
    lowest_rating = min(normalized_ratings)
    highest_rating = max(normalized_ratings)
    disagreement_spread = highest_rating - lowest_rating

    if ratings_count >= GROUP_SCORE_MIN_RATINGS_FOR_OUTLIER_SOFTENING:
        base_ratings = normalized_ratings[:-1]
        base_rating = sum(base_ratings) / len(base_ratings)
        disagreement_penalty = (base_rating - lowest_rating) * GROUP_SCORE_OUTLIER_PENALTY
        effective_rating = base_rating - disagreement_penalty
    else:
        base_rating = average_rating
        disagreement_penalty = 0.0
        effective_rating = average_rating

    conflict_flag = (
        ratings_count >= GROUP_SCORE_MIN_RATINGS_FOR_OUTLIER_SOFTENING
        and lowest_rating <= 1.0
        and (base_rating - lowest_rating) >= 3.0
    )

    return RecipePreferenceScoreSummary(
        ratings_count=ratings_count,
        average_rating=_round_rating(average_rating),
        effective_rating=_round_rating(max(0.0, min(5.0, effective_rating))),
        median_rating=_round_rating(median_rating),
        lowest_rating=_round_rating(lowest_rating),
        highest_rating=_round_rating(highest_rating),
        base_rating=_round_rating(base_rating),
        disagreement_penalty=_round_rating(disagreement_penalty),
        disagreement_spread=_round_rating(disagreement_spread),
        conflict_flag=conflict_flag,
    )


def build_recipe_preference_score_summary(
    preferences: Sequence[RecipePreference],
) -> RecipePreferenceScoreSummary:
    ratings = [preference.rating for preference in preferences]
    return build_recipe_preference_score_summary_from_ratings(ratings)