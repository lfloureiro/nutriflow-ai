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

export type FamilyMember = {
  id: number;
  name: string;
  household_id: number;
};

export type Household = {
  id: number;
  name: string;
  members: FamilyMember[];
};

export type MealFeedback = {
  id: number;
  meal_plan_item_id: number;
  reaction: "gostou" | "neutro" | "nao_gostou";
  note: string | null;
  family_member: FamilyMember;
};

export type RecipeFeedbackSummary = {
  recipe_id: number;
  recipe_name: string;
  total_feedback: number;
  liked_count: number;
  neutral_count: number;
  disliked_count: number;
  acceptance_score: number;
};