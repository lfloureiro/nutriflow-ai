from datetime import UTC, datetime

from backend.app.models.family_member import FamilyMember
from backend.app.models.recipe_preference import RecipePreference
from backend.app.services.auto_meal_planner import build_preference_map
from backend.app.services.recipe_preference_scoring import (
    build_recipe_preference_score_summary_from_ratings,
)


def test_group_score_softens_single_low_outlier():
    summary = build_recipe_preference_score_summary_from_ratings([5, 5, 5, 0])

    assert summary.ratings_count == 4
    assert summary.average_rating == 3.75
    assert summary.base_rating == 5.0
    assert summary.disagreement_penalty == 0.75
    assert summary.effective_rating == 4.25
    assert summary.median_rating == 5.0
    assert summary.lowest_rating == 0.0
    assert summary.highest_rating == 5.0
    assert summary.disagreement_spread == 5.0
    assert summary.conflict_flag is True


def test_group_score_uses_simple_average_for_three_or_fewer_ratings():
    summary = build_recipe_preference_score_summary_from_ratings([5, 5, 0])

    assert summary.ratings_count == 3
    assert summary.average_rating == 3.33
    assert summary.base_rating == 3.33
    assert summary.disagreement_penalty == 0.0
    assert summary.effective_rating == 3.33
    assert summary.conflict_flag is False


def test_recipe_preference_summary_endpoint_returns_effective_group_score(
    client,
    db_session,
    sample_data,
):
    household_id = sample_data["household_2_id"]
    recipe_id = sample_data["recipe_1_id"]

    member_4 = FamilyMember(name="Diogo", household_id=household_id)
    member_5 = FamilyMember(name="Eva", household_id=household_id)
    member_6 = FamilyMember(name="Filipa", household_id=household_id)

    db_session.add_all([member_4, member_5, member_6])
    db_session.commit()

    existing_member_id = sample_data["member_3_id"]

    preferences = [
        RecipePreference(
            household_id=household_id,
            family_member_id=existing_member_id,
            recipe_id=recipe_id,
            rating=5,
            note="Adora",
            updated_at=datetime.now(UTC),
        ),
        RecipePreference(
            household_id=household_id,
            family_member_id=member_4.id,
            recipe_id=recipe_id,
            rating=5,
            note="Muito bom",
            updated_at=datetime.now(UTC),
        ),
        RecipePreference(
            household_id=household_id,
            family_member_id=member_5.id,
            recipe_id=recipe_id,
            rating=5,
            note="Excelente",
            updated_at=datetime.now(UTC),
        ),
        RecipePreference(
            household_id=household_id,
            family_member_id=member_6.id,
            recipe_id=recipe_id,
            rating=0,
            note="Não gosta",
            updated_at=datetime.now(UTC),
        ),
    ]
    db_session.add_all(preferences)
    db_session.commit()

    response = client.get(
        f"/recipe-preferences/households/{household_id}/recipes/{recipe_id}/summary"
    )
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["ratings_count"] == 4
    assert body["average_rating"] == 4.25
    assert body["simple_average_rating"] == 3.75
    assert body["median_rating"] == 5.0
    assert body["lowest_rating"] == 0.0
    assert body["highest_rating"] == 5.0
    assert body["base_rating"] == 5.0
    assert body["disagreement_penalty"] == 0.75
    assert body["disagreement_spread"] == 5.0
    assert body["conflict_flag"] is True


def test_build_preference_map_uses_effective_group_score(
    db_session,
    sample_data,
):
    household_id = sample_data["household_2_id"]
    recipe_id = sample_data["recipe_2_id"]

    member_4 = FamilyMember(name="Guilherme", household_id=household_id)
    member_5 = FamilyMember(name="Helena", household_id=household_id)
    member_6 = FamilyMember(name="Ines", household_id=household_id)

    db_session.add_all([member_4, member_5, member_6])
    db_session.commit()

    preferences = [
        RecipePreference(
            household_id=household_id,
            family_member_id=sample_data["member_3_id"],
            recipe_id=recipe_id,
            rating=5,
            note=None,
            updated_at=datetime.now(UTC),
        ),
        RecipePreference(
            household_id=household_id,
            family_member_id=member_4.id,
            recipe_id=recipe_id,
            rating=5,
            note=None,
            updated_at=datetime.now(UTC),
        ),
        RecipePreference(
            household_id=household_id,
            family_member_id=member_5.id,
            recipe_id=recipe_id,
            rating=4,
            note=None,
            updated_at=datetime.now(UTC),
        ),
        RecipePreference(
            household_id=household_id,
            family_member_id=member_6.id,
            recipe_id=recipe_id,
            rating=0,
            note=None,
            updated_at=datetime.now(UTC),
        ),
    ]
    db_session.add_all(preferences)
    db_session.commit()

    preference_map = build_preference_map(db_session, household_id)

    assert recipe_id in preference_map
    assert preference_map[recipe_id]["average_rating"] == 3.97
    assert preference_map[recipe_id]["simple_average_rating"] == 3.5
    assert preference_map[recipe_id]["ratings_count"] == 4
    assert preference_map[recipe_id]["conflict_flag"] is True