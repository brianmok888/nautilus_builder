/**
 * @deprecated Use apiFetch and the typed functions from api.ts instead.
 * This module is retained for backward compatibility only.
 * New code must use the canonical api.ts functions.
 */

/**
 * Builder API client with error handling for 429/422/404 responses.
 * Centralises fetch logic so components don't duplicate error handling.
 */

export interface ApiClientError {
  status: number;
  error: string;
  details?: string;
}

export class BuilderApiError extends Error {
  status: number;
  apiError: string;
  details?: string;

  constructor(status: number, error: string, details?: string) {
    super(`API ${status}: ${error}`);
    this.status = status;
    this.apiError = error;
    this.details = details;
  }
}

export async function apiPost<T = Record<string, unknown>>(
  path: string,
  body: Record<string, unknown>,
): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let error = "Request failed";
    let details: string | undefined;
    try {
      const json = await response.json();
      error = json.error ?? error;
      details = json.details;
    } catch {
      // Non-JSON error, use status text
      error = response.statusText || error;
    }
    throw new BuilderApiError(response.status, error, details);
  }

  return response.json() as Promise<T>;
}

export async function apiGet<T = Record<string, unknown>>(path: string): Promise<T> {
  const response = await fetch(path);

  if (!response.ok) {
    let error = "Request failed";
    let details: string | undefined;
    try {
      const json = await response.json();
      error = json.error ?? error;
      details = json.details;
    } catch {
      error = response.statusText || error;
    }
    throw new BuilderApiError(response.status, error, details);
  }

  return response.json() as Promise<T>;
}

export function isRateLimitError(error: unknown): error is BuilderApiError {
  return error instanceof BuilderApiError && error.status === 429;
}

export function isNotFoundError(error: unknown): error is BuilderApiError {
  return error instanceof BuilderApiError && error.status === 404;
}

export function isValidationError(error: unknown): error is BuilderApiError {
  return error instanceof BuilderApiError && error.status === 422;
}
