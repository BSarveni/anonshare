import axios from 'axios'

export function formatApiError(err: unknown, fallback: string): string {
  if (!axios.isAxiosError(err)) {
    return fallback
  }
  if (!err.response) {
    return 'Cannot reach the API. Set VITE_API_URL to your Railway API URL and redeploy the frontend.'
  }

  const detail = err.response.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item?.msg === 'string' ? item.msg : JSON.stringify(item)))
      .join(', ')
  }

  return `${fallback} (HTTP ${err.response.status})`
}
