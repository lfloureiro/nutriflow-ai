from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.ingredient import Ingredient
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient
from backend.app.schemas.recipe import RecipeCreate, RecipeRead, RecipeDetail
from backend.app.schemas.recipe_ingredient import RecipeIngredientCreate

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=list[RecipeRead])
def list_recipes(db: Session = Depends(get_db)):
    recipes = db.query(Recipe).order_by(Recipe.id.asc()).all()
    return recipes


@router.get("/{recipe_id}", response_model=RecipeDetail)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = (
        db.query(Recipe)
        .options(
            joinedload(Recipe.ingredient_links).joinedload(RecipeIngredient.ingredient)
        )
        .filter(Recipe.id == recipe_id)
        .first()
    )

    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    return recipe


@router.post("/", response_model=RecipeRead, status_code=201)
def create_recipe(recipe_in: RecipeCreate, db: Session = Depends(get_db)):
    name_clean = recipe_in.name.strip()

    if not name_clean:
        raise HTTPException(status_code=400, detail="O nome da receita é obrigatório.")

    recipe = Recipe(
        name=name_clean,
        description=recipe_in.description,
    )

    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    return recipe


@router.post("/{recipe_id}/ingredients", response_model=RecipeDetail, status_code=201)
def add_ingredient_to_recipe(
    recipe_id: int,
    data: RecipeIngredientCreate,
    db: Session = Depends(get_db),
):
    recipe = (
        db.query(Recipe)
        .options(
            joinedload(Recipe.ingredient_links).joinedload(RecipeIngredient.ingredient)
        )
        .filter(Recipe.id == recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    ingredient = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado.")

    existing_link = (
        db.query(RecipeIngredient)
        .filter(
            RecipeIngredient.recipe_id == recipe_id,
            RecipeIngredient.ingredient_id == data.ingredient_id,
        )
        .first()
    )
    if existing_link:
        raise HTTPException(
            status_code=400,
            detail="Esse ingrediente já está associado a esta receita.",
        )

    link = RecipeIngredient(
        recipe_id=recipe_id,
        ingredient_id=data.ingredient_id,
        quantity=data.quantity,
        unit=data.unit,
    )

    db.add(link)
    db.commit()

    recipe = (
        db.query(Recipe)
        .options(
            joinedload(Recipe.ingredient_links).joinedload(RecipeIngredient.ingredient)
        )
        .filter(Recipe.id == recipe_id)
        .first()
    )

    return recipe