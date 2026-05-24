import { useEffect, useState } from 'react'
import { adminApi, type FlaggedEvent } from '../lib/api'

export default function AdminPage() {
  const [flags, setFlags] = useState<FlaggedEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadFlags() {
    setLoading(true)
    try {
      const { data } = await adminApi.flags()
      setFlags(data)
    } catch {
      setError('Could not load flagged events')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFlags()
  }, [])

  async function handleBan(userId: string) {
    await adminApi.ban(userId)
    await loadFlags()
  }

  async function handleResolve(flagId: string) {
    await adminApi.resolve(flagId)
    await loadFlags()
  }

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-slate-900">Admin — flagged events</h1>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {loading ? (
        <p className="mt-8 text-sm text-slate-500">Loading…</p>
      ) : (
        <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">User</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Detail</th>
                <th className="px-4 py-3 font-medium">When</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {flags.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-slate-500">
                    No unresolved flags
                  </td>
                </tr>
              )}
              {flags.map((f) => (
                <tr key={f.id} className="bg-white">
                  <td className="px-4 py-3 font-medium text-slate-900">{f.user_pseudonym}</td>
                  <td className="px-4 py-3 text-slate-600">{f.event_type}</td>
                  <td className="max-w-xs truncate px-4 py-3 text-slate-600" title={f.detail}>
                    {f.detail}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(f.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleBan(f.user_id)}
                        className="rounded border border-red-200 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                      >
                        Ban user
                      </button>
                      <button
                        type="button"
                        onClick={() => handleResolve(f.id)}
                        className="rounded border border-slate-200 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
                      >
                        Resolve
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
