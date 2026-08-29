import axios from "axios";
import type { AxiosError, AxiosInstance } from "axios";
import type { ApiError } from "../types/api";
import { API_BASE_URL } from "../utils/constants";

const REQUEST_TIMEOUT_MS = 10000;

/**
 * Centralized Axios instance. All service modules should import this
 * client rather than calling axios directly, so the base URL,
 * timeout, and error handling stay consistent across the app.
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: {
    Accept: "application/json",
  },
});

/**
 * Normalizes any Axios error into the app's ApiError shape so
 * consumers never have to branch on Axios-specific error types.
 */
function normalizeError(error: AxiosError): ApiError {
  if (error.response) {
    const data = error.response.data as
      | { detail?: string; message?: string }
      | undefined;
    return {
      message: data?.detail ?? data?.message ?? error.message,
      statusCode: error.response.status,
    };
  }

  if (error.request) {
    return {
      message: "No response received from the server. Check your connection.",
      statusCode: 0,
    };
  }

  return {
    message: error.message || "An unexpected error occurred.",
    statusCode: 0,
  };
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => Promise.reject(normalizeError(error))
);
