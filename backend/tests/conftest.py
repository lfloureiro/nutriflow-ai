from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.family_member import FamilyMember
from backend.app.models.household import Household
from backend.app.models.ingredient import Ingredient
from backend.app.models.meal_feedback import MealFeedback
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient
from backend.app.models.recipe_preference import RecipePreference


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db: Session = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db: Session = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_data(db_session: Session):
    household_1 = Household(name="Casa A")
    household_2 = Household(name="Casa B")
    household_3 = Household(name="Casa Sem Membros Com Plano")
    household_4 = Household(name="Casa Vazia")

    db_session.add_all([household_1, household_2, household_3, household_4])
    db_session.commit()

    member_1 = FamilyMember(name="Ana", household_id=household_1.id)
    member_2 = FamilyMember(name="Bruno", household_id=household_1.id)
    member_3 = FamilyMember(name="Carla", household_id=household_2.id)

    db_session.add_all([member_1, member_2, member_3])
    db_session.commit()

    recipe_1 = Recipe(name="Massa com Atum", description="Receita de teste")
    recipe_2 = Recipe(name="Frango no Forno", description="Receita de teste")

    db_session.add_all([recipe_1, recipe_2])
    db_session.commit()

    ingredient_1 = Ingredient(name="Atum")
    ingredient_2 = Ingredient(name="Massa")

    db_session.add_all([ingredient_1, ingredient_2])
    db_session.commit()

    link_1 = RecipeIngredient(
        recipe_id=recipe_1.id,
        ingredient_id=ingredient_1.id,
        quantity="1",
        unit="lata",
    )
    link_2 = RecipeIngredient(
        recipe_id=recipe_1.id,
        ingredient_id=ingredient_2.id,
        quantity="250",
        unit="g",
    )

    db_session.add_all([link_1, link_2])
    db_session.commit()

    meal_household_1 = MealPlanItem(
        household_id=household_1.id,
        plan_date=date(2026, 5, 10),
        meal_type="jantar",
        notes="Refeição HH1",
        recipe_id=recipe_1.id,
    )

    meal_household_3 = MealPlanItem(
        household_id=household_3.id,
        plan_date=date(2026, 5, 11),
        meal_type="almoco",
        notes="Plano sem membros",
        recipe_id=recipe_2.id,
    )

    db_session.add_all([meal_household_1, meal_household_3])
    db_session.commit()

    preference_member_1 = RecipePreference(
        household_id=household_1.id,
        family_member_id=member_1.id,
        recipe_id=recipe_1.id,
        rating=4,
        note="Gosta bastante",
        updated_at=datetime.now(UTC),
    )

    db_session.add(preference_member_1)
    db_session.commit()

    db_session.refresh(household_1)
    db_session.refresh(household_2)
    db_session.refresh(household_3)
    db_session.refresh(household_4)
    db_session.refresh(member_1)
    db_session.refresh(member_2)
    db_session.refresh(member_3)
    db_session.refresh(recipe_1)
    db_session.refresh(recipe_2)
    db_session.refresh(meal_household_1)
    db_session.refresh(meal_household_3)

    return {
        "household_1_id": household_1.id,
        "household_2_id": household_2.id,
        "household_3_id": household_3.id,
        "household_4_id": household_4.id,
        "member_1_id": member_1.id,
        "member_2_id": member_2.id,
        "member_3_id": member_3.id,
        "recipe_1_id": recipe_1.id,
        "recipe_2_id": recipe_2.id,
        "meal_household_1_id": meal_household_1.id,
        "meal_household_3_id": meal_household_3.id,
    }