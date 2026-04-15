from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.ingredient import Ingredient
from backend.app.schemas.ingredient import IngredientCreate, IngredientRead

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/", response_model=list[IngredientRead])
def list_ingredients(db: Session = Depends(get_db)):
    ingredients = db.query(Ingredient).order_by(Ingredient.name.asc()).all()
    return ingredients


@router.post("/", response_model=IngredientRead, status_code=201)
def create_ingredient(ingredient_in: IngredientCreate, db: Session = Depends(get_db)):
    name_clean = ingredient_in.name.strip()

    if not name_clean:
        raise HTTPException(status_code=400, detail="O nome do ingrediente é obrigatório.")

    existing = db.query(Ingredient).filter(Ingredient.name == name_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Esse ingrediente já existe.")

    ingredient = Ingredient(name=name_clean)
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    return ingredient