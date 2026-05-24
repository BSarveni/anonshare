import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Modal from '../components/Modal'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../lib/api'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [pseudonym, setPseudonym] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { data } = await authApi.register(password)
      await login(data.access_token)
      setPseudonym(data.pseudonym)
    } catch {
      setError('Registration failed. Use at least 8 characters.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-md">
        <h1 className="text-xl font-semibold text-slate-900">Join AnonShare</h1>
        <p className="mt-1 text-sm text-slate-500">Choose a password — we assign your pseudonym.</p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              required
              minLength={8}
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
            {loading ? 'Creating…' : 'Register'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Have a pseudonym?{' '}
          <Link to="/login" className="font-medium text-slate-900 hover:underline">
            Log in
          </Link>
        </p>
      </div>

      <Modal
        open={!!pseudonym}
        title="Save your identity"
        primaryLabel="Go to feed"
        onPrimary={() => navigate('/feed')}
      >
        <p>
          Your anonymous identity is:{' '}
          <strong className="text-slate-900">{pseudonym}</strong>
        </p>
        <p className="mt-3 font-medium text-amber-700">
          Write this down — you cannot recover it.
        </p>
      </Modal>
    </div>
  )
}
