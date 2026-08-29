/**
 * Normalized error shape surfaced by the API client. Every rejected
 * service call resolves to this, regardless of whether the failure
 * came from the network, a timeout, or a non-2xx response.
 */
export interface ApiError {
  message: string;
  statusCode: number;
}

/**
 * Generic wrapper for a successful API response, used by the service
 * layer so callers get both the payload and the HTTP status.
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
}
