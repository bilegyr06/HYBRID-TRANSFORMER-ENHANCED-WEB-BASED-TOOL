/**
 * TypeScript interfaces for authentication and user management.
 * Supporting feature: Type safety for authentication features.
 */

export interface User {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
  last_login: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SavedReview {
  id: number;
  user_id: number;
  title: string | null;
  input_abstracts_count: number;
  extractive_summary: string;
  abstractive_summary: string;
  key_themes: string[] | null;
  visualizations_metadata: Record<string, unknown> | null;
  rouge_scores: Record<string, number> | null;
  created_at: string;
  updated_at: string;
}

export interface SavedReviewListItem {
  id: number;
  title: string | null;
  input_abstracts_count: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedReviewsResponse {
  reviews: SavedReviewListItem[];
  total_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
