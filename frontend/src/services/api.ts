export interface RecommendationRequest {
  area: string;
  budget_inr: number;
  cuisine: string;
  min_rating: number;
  notes?: string;
  top_n: number;
}

export interface RestaurantResult {
  restaurant_id: string;
  name: string;
  cuisines: string[];
  rating: number;
  estimated_cost: number | string;
  reason: string;
  match_signals?: string[];
}

export interface RecommendationResponse {
  request_id: string;
  results: RestaurantResult[];
}

const API_BASE_URL = 'http://localhost:8000';

export async function fetchRecommendations(req: RecommendationRequest): Promise<RecommendationResponse> {
  const response = await fetch(`${API_BASE_URL}/recommendations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchExplore(cuisine?: string): Promise<RecommendationResponse> {
  const params = new URLSearchParams({ limit: '6' });
  if (cuisine) params.set('cuisine', cuisine);
  const response = await fetch(`${API_BASE_URL}/explore?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json();
}
