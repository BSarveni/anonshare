import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../lib/api'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [pseudonym, setPseudonym] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { data } = await authApi.login(pseudonym, password)
      await login(data.access_token)
      navigate('/feed')
    } catch {
      setError('Invalid pseudonym or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-md">
        <h1 className="text-xl font-semibold text-slate-900">Log in</h1>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Pseudonym</label>
            <input
              required
              value={pseudonym}
              onChange={(e) => setPseudonym(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400"
              placeholder="SwiftOtter_4821"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-slate-900 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Log in'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          New here?{' '}
          <Link to="/register" className="font-medium text-slate-900 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
