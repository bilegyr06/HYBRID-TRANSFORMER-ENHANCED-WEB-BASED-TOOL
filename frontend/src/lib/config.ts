const rawApiRoot = import.meta.env.VITE_API_ROOT || 'http://localhost:8000';

export const API_ROOT = rawApiRoot.replace(/\/$/, '');
export const API_BASE_URL = `${API_ROOT}/api`;
export const AUTH_BASE_URL = `${API_ROOT}/auth`;
export const REVIEWS_BASE_URL = `${API_ROOT}/reviews`;
