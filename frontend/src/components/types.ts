export type Recipe = {
  id: number;
  name: string;
  description: string | null;
};

export type Ingredient = {
  id: number;
  name: string;
};

export type MealPlanItem = {
  id: number;
  plan_date: string;
  meal_type: string;
  notes: string | null;
  recipe: Recipe;
};

export type ShoppingListSource = {
  recipe_id: number;
  recipe_name: string;
  plan_date: string;
  meal_type: string;
};

export type ShoppingListItem = {
  ingredient_id: number;
  ingredient_name: string;
  quantity: string | null;
  unit: string | null;
  sources: ShoppingListSource[];
};