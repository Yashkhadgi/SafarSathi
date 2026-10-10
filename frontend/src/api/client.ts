/**
 * Safe, centralized API client with automatic credential handling,
 * cookie credentials, and typed error responses.
 */

export interface ApiErrorResponse {
  detail?: string;
  error?: string;
  message?: string;
  retry_after?: number;
}

export class ApiError extends Error {
  status: number;
  data: ApiErrorResponse;

  constructor(status: number, data: ApiErrorResponse) {
    super(data.detail || data.error || data.message || `API error with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

const API_BASE = '/api/v1';

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorData: ApiErrorResponse = {};
    try {
      errorData = await res.json();
    } catch {
      errorData = { error: res.statusText || 'Unknown network error' };
    }
    throw new ApiError(res.status, errorData);
  }

  // Handle empty bodies (204 No Content)
  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}

export async function apiGet<T>(path: string, customHeaders?: HeadersInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      ...customHeaders,
    },
    credentials: 'include',
  });
  return parseResponse<T>(res);
}

export async function apiPost<T>(path: string, body?: unknown, customHeaders?: HeadersInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...customHeaders,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });
  return parseResponse<T>(res);
}

export async function apiPatch<T>(path: string, body?: unknown, customHeaders?: HeadersInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...customHeaders,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });
  return parseResponse<T>(res);
}

export async function apiPut<T>(path: string, body?: unknown, customHeaders?: HeadersInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...customHeaders,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });
  return parseResponse<T>(res);
}

export async function apiDelete<T>(path: string, body?: unknown, customHeaders?: HeadersInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...customHeaders,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });
  return parseResponse<T>(res);
}
