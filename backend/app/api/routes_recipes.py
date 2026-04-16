from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.ingredient import Ingredient
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient
from backend.app.schemas.recipe import RecipeCreate, RecipeRead, RecipeDetail, RecipeUpdate
from backend.app.schemas.recipe_ingredient import (
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
)

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


@router.patch("/{recipe_id}", response_model=RecipeRead)
def update_recipe(
    recipe_id: int,
    recipe_in: RecipeUpdate,
    db: Session = Depends(get_db),
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    if recipe_in.name is not None:
        name_clean = recipe_in.name.strip()
        if not name_clean:
            raise HTTPException(status_code=400, detail="O nome da receita é obrigatório.")
        recipe.name = name_clean

    if "description" in recipe_in.model_fields_set:
        recipe.description = recipe_in.description

    db.commit()
    db.refresh(recipe)

    return recipe


@router.delete("/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    db.delete(recipe)
    db.commit()

    return {"message": "Receita apagada com sucesso."}


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


@router.patch("/{recipe_id}/ingredients/{link_id}", response_model=RecipeDetail)
def update_recipe_ingredient(
    recipe_id: int,
    link_id: int,
    data: RecipeIngredientUpdate,
    db: Session = Depends(get_db),
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    link = (
        db.query(RecipeIngredient)
        .filter(
            RecipeIngredient.id == link_id,
            RecipeIngredient.recipe_id == recipe_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Ligação ingrediente-receita não encontrada.")

    new_ingredient_id = data.ingredient_id if data.ingredient_id is not None else link.ingredient_id

    if data.ingredient_id is not None:
        ingredient = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingrediente não encontrado.")

        existing = (
            db.query(RecipeIngredient)
            .filter(
                RecipeIngredient.recipe_id == recipe_id,
                RecipeIngredient.ingredient_id == new_ingredient_id,
                RecipeIngredient.id != link_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Esse ingrediente já está associado a esta receita.",
            )

        link.ingredient_id = new_ingredient_id

    if "quantity" in data.model_fields_set:
        link.quantity = data.quantity

    if "unit" in data.model_fields_set:
        link.unit = data.unit

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


@router.delete("/{recipe_id}/ingredients/{link_id}", response_model=RecipeDetail)
def delete_recipe_ingredient(
    recipe_id: int,
    link_id: int,
    db: Session = Depends(get_db),
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    link = (
        db.query(RecipeIngredient)
        .filter(
            RecipeIngredient.id == link_id,
            RecipeIngredient.recipe_id == recipe_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Ligação ingrediente-receita não encontrada.")

    db.delete(link)
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