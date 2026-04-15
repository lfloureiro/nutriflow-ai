from pydantic import BaseModel, ConfigDict


class IngredientCreate(BaseModel):
    name: str


class IngredientRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)