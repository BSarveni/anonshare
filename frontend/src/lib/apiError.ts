import axios from 'axios'

import { apiBaseUrl, apiRegisterUrl } from './api'

export function formatApiError(err: unknown, fallback: string): string {
  if (!axios.isAxiosError(err)) {
    return fallback
  }
  if (!err.response) {
    const target = apiRegisterUrl()
    if (!apiBaseUrl) {
      return (
        'VITE_API_URL is empty in this build. Set it in Railway frontend variables, then Redeploy ' +
        'the frontend service (variables are baked in at build time).'
      )
    }
    return (
      `Cannot reach the API at ${target}. Usually CORS or a wrong API URL. ` +
      'Open that /health URL in your browser. On the api service set ALLOWED_ORIGINS to your ' +
      `frontend URL (e.g. ${window.location.origin}), redeploy api, then redeploy frontend.`
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
