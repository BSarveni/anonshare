import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { groupsApi, type Group } from '../lib/api'

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([])
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadGroups() {
    setLoading(true)
    try {
      const { data } = await groupsApi.list()
      setGroups(data)
    } catch {
      setError('Could not load groups')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadGroups()
  }, [])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setCreating(true)
    setError(null)
    try {
      await groupsApi.create(name.trim())
      setName('')
      await loadGroups()
    } catch {
      setError('Could not create group')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-slate-900">Groups</h1>

      <form onSubmit={handleCreate} className="mt-6 flex max-w-md gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New group name"
          className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400"
        />
        <button
          type="submit"
          disabled={creating}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          Create
        </button>
      </form>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      {loading ? (
        <p className="mt-8 text-sm text-slate-500">Loading…</p>
      ) : (
        <ul className="mt-8 divide-y divide-slate-200 rounded-xl border border-slate-200">
          {groups.length === 0 && (
            <li className="px-4 py-6 text-sm text-slate-500">No groups yet. Create one above.</li>
          )}
          {groups.map((g) => (
            <li key={g.id}>
              <Link
                to={`/groups/${g.id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-50"
              >
                <span className="font-medium text-slate-900">{g.name}</span>
                <span className="text-xs text-slate-400">
                  {new Date(g.created_at).toLocaleDateString()}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
