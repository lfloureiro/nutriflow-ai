export type RecipeCategory =
  | "carne"
  | "peixe"
  | "vegetariano_leguminosas"
  | "outra";

export type RecipeProtein =
  | "frango"
  | "vaca"
  | "porco"
  | "peru"
  | "enchidos_processados"
  | "peixe"
  | "ovos"
  | "leguminosas"
  | "queijo_lacticinios"
  | "outra"
  | "nenhuma";

export type RecipeMealSuitability = "almoco" | "jantar" | "ambos";

export const RECIPE_CATEGORY_OPTIONS: Array<{
  value: RecipeCategory;
  label: string;
}> = [
  { value: "carne", label: "Carne" },
  { value: "peixe", label: "Peixe" },
  { value: "vegetariano_leguminosas", label: "Vegetariano / leguminosas" },
  { value: "outra", label: "Outra" },
];

export const RECIPE_PROTEIN_OPTIONS: Array<{
  value: RecipeProtein;
  label: string;
}> = [
  { value: "frango", label: "Frango" },
  { value: "vaca", label: "Vaca" },
  { value: "porco", label: "Porco" },
  { value: "peru", label: "Peru" },
  { value: "enchidos_processados", label: "Enchidos / processados" },
  { value: "peixe", label: "Peixe" },
  { value: "ovos", label: "Ovos" },
  { value: "leguminosas", label: "Leguminosas" },
  { value: "queijo_lacticinios", label: "Queijo / lacticínios" },
  { value: "outra", label: "Outra" },
  { value: "nenhuma", label: "Nenhuma" },
];

export const RECIPE_MEAL_SUITABILITY_OPTIONS: Array<{
  value: RecipeMealSuitability;
  label: string;
}> = [
  { value: "almoco", label: "Almoço" },
  { value: "jantar", label: "Jantar" },
  { value: "ambos", label: "Ambos" },
];

export type Recipe = {
  id: number;
  name: string;
  description: string | null;
  categoria_alimentar: RecipeCategory | null;
  proteina_principal: RecipeProtein | null;
  adequado_refeicao: RecipeMealSuitability | null;
  auto_plan_enabled: boolean;
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
  in_cart: boolean;
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