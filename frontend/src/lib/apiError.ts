import axios from 'axios'

export function formatApiError(err: unknown, fallback: string): string {
  if (!axios.isAxiosError(err)) {
    return fallback
  }
  if (!err.response) {
    return (
      'Cannot reach the API (network/CORS). Check: (1) VITE_API_URL is your Railway API URL, ' +
      '(2) frontend was redeployed after setting it, (3) API /health works in the browser, ' +
      '(4) ALLOWED_ORIGINS on the API includes your frontend URL.'
    )
  }
  if (err.response.status === 502 || err.response.status === 503) {
    return (
      'API is not responding (502/503). In Railway: open the api service → Deploy logs → confirm ' +
      'the port in "Starting on port X" matches Networking target port; confirm DATABASE_URL is set.'
    )
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
