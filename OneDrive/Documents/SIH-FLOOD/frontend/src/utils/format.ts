/**
 * Formats an ISO date string (as returned by the API) into a
 * human-readable form, e.g. "14 Jul 2026".
 */
export function formatEventDate(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

/**
 * Formats a number with locale-aware thousands separators.
 * Returns a fallback string when the value is null/undefined.
 */
export function formatNumber(
  value: number | null | undefined,
  fallback: string = "N/A"
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return fallback;
  }
  return new Intl.NumberFormat("en-US").format(value);
}

/**
 * Formats a numeric value as a percentage string.
 * Set `isFraction` to true if the input is already expressed as 0-1
 * rather than 0-100.
 */
export function formatPercentage(
  value: number | null | undefined,
  isFraction: boolean = false,
  fractionDigits: number = 1
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  const normalized = isFraction ? value * 100 : value;
  return `${normalized.toFixed(fractionDigits)}%`;
}
