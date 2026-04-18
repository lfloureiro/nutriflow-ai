import { API_BASE_URL } from "../config";

export type RecipePreference = {
  id: number;
  household_id: number;
  recipe_id: number;
  rating: number;
  note: string | null;
  updated_at: string;
  family_member: {
    id: number;
    name: string;
    household_id: number;
  };
};

export type RecipePreferenceSummary = {
  household_id: number;
  recipe_id: number;
  recipe_name: string;
  ratings_count: number;
  average_rating: number;
  ratings: RecipePreference[];
};

async function parseJsonResponse<T>(
  res: Response,
  fallbackMessage: string
): Promise<T> {
  const data = await res.json();

  if (!res.ok) {
    const detail =
      data &&
      typeof data === "object" &&
      "detail" in data &&
      typeof (data as { detail?: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : fallbackMessage;

    throw new Error(detail);
  }

  return data as T;
}

export async function listRecipePreferences(
  householdId: number,
  recipeId: number
): Promise<RecipePreference[]> {
  const res = await fetch(
    `${API_BASE_URL}/recipe-preferences/households/${householdId}/recipes/${recipeId}`
  );

  return parseJsonResponse<RecipePreference[]>(
    res,
    "Não foi possível carregar as avaliações da receita."
  );
}

export async function upsertRecipePreference(
  householdId: number,
  recipeId: number,
  memberId: number,
  payload: { rating: number; note?: string | null }
): Promise<RecipePreference> {
  const res = await fetch(
    `${API_BASE_URL}/recipe-preferences/households/${householdId}/recipes/${recipeId}/members/${memberId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return parseJsonResponse<RecipePreference>(
    res,
    "Não foi possível guardar a avaliação."
  );
}

export async function deleteRecipePreference(
  householdId: number,
  recipeId: number,
  memberId: number
): Promise<{ message: string }> {
  const res = await fetch(
    `${API_BASE_URL}/recipe-preferences/households/${householdId}/recipes/${recipeId}/members/${memberId}`,
    {
      method: "DELETE",
    }
  );

  return parseJsonResponse<{ message: string }>(
    res,
    "Não foi possível apagar a avaliação."
  );
}

export async function getRecipePreferenceSummary(
  householdId: number,
  recipeId: number
): Promise<RecipePreferenceSummary> {
  const res = await fetch(
    `${API_BASE_URL}/recipe-preferences/households/${householdId}/recipes/${recipeId}/summary`
  );

  return parseJsonResponse<RecipePreferenceSummary>(
    res,
    "Não foi possível carregar o score da receita."
  );
}

export async function listHouseholdRecipeSummaries(
  householdId: number
): Promise<RecipePreferenceSummary[]> {
  const res = await fetch(
    `${API_BASE_URL}/recipe-preferences/households/${householdId}/summaries`
  );

  return parseJsonResponse<RecipePreferenceSummary[]>(
    res,
    "Não foi possível carregar os scores da família."
  );
}