import axios from 'axios';
import { API_BASE_URL, REVIEWS_BASE_URL } from './config';
import type { 
  UploadResponse, 
  ProcessResponse, 
  ProcessRequest,   // now it will be used
  AnalysisRequest,
  AnalysisResponse,
  ExtractThemesResponse,
  Metrics,
  SynthesisApiResponse,
  SynthesisResult
} from '../types';

export interface SaveReviewRequest {
  title?: string;
  input_abstracts_count: number;
  extractive_summary: string;
  abstractive_summary: string;
  key_themes?: string[];
  visualizations_metadata?: Record<string, unknown>;
  rouge_scores?: Metrics;
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

export interface SavedReviewResponse {
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

export interface SynthesisRequest {
  extractive_sentences?: Array<{
    text: string;
    doc_id?: string;
    sentence_id?: number;
    score?: number;
  }>;
  documents?: Record<string, string>;
  action?: 'synthesize' | 'regenerate' | 'export' | 'save';
  regen_k?: number;
  export_format?: 'md' | 'docx';
  title?: string;
}

// Main axios instance with credentials for JWT cookie handling
// Supporting feature: User authentication via httpOnly cookies
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // Send/receive httpOnly cookies with every request
});

// Add 401 interceptor to handle unauthorized responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // If 401 Unauthorized, user's token is invalid or expired
    if (error.response?.status === 401) {
      // Clear auth state and redirect to login
      // This will be handled by the component using the API
      console.log('Unauthorized - please login again');
    }
    return Promise.reject(error);
  }
);

export const uploadFiles = async (files: File[]): Promise<UploadResponse> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const res = await api.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const processFiles = async (filenames: string[] = []): Promise<ProcessResponse> => {
  const payload: ProcessRequest = { filenames };
  const res = await api.post<ProcessResponse>('/process', payload);
  return res.data;
};

export const analyzeResults = async (payload: AnalysisRequest): Promise<AnalysisResponse> => {
  const res = await api.post<AnalysisResponse>('/analysis/results', payload);
  return res.data;
};

export const extractThemes = async (text: string): Promise<string[]> => {
  const res = await api.post<ExtractThemesResponse>('/extract-themes', { text });
  return res.data.themes;
};

const reviewsApi = axios.create({
  baseURL: REVIEWS_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

export const saveReview = async (payload: SaveReviewRequest): Promise<SavedReviewResponse> => {
  const res = await reviewsApi.post<SavedReviewResponse>('/save', payload);
  return res.data;
};

export const getMyReviews = async (): Promise<PaginatedReviewsResponse> => {
  const res = await reviewsApi.get<PaginatedReviewsResponse>('/');
  return res.data;
};

export const getMyReview = async (reviewId: number): Promise<SavedReviewResponse> => {
  const res = await reviewsApi.get<SavedReviewResponse>(`/${reviewId}`);
  return res.data;
};

export const synthesizeMultiDocument = async (payload: SynthesisRequest): Promise<SynthesisApiResponse> => {
  const res = await api.post<SynthesisApiResponse>('/synthesize/multi-document', payload);
  return res.data;
};

export type { SynthesisResult };
