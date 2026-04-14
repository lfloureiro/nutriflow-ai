from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.recipe import Recipe
from backend.app.schemas.recipe import RecipeCreate, RecipeRead

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=list[RecipeRead])
def list_recipes(db: Session = Depends(get_db)):
    recipes = db.query(Recipe).order_by(Recipe.id.asc()).all()
    return recipes


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