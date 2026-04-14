from pydantic import BaseModel, ConfigDict


class RecipeCreate(BaseModel):
    name: str
    description: str | None = None


class RecipeRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)