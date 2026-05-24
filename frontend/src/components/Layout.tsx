import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `block rounded-lg px-3 py-2 text-sm transition ${
    isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
  }`

export default function Layout() {
  const { user, logout, isAdmin } = useAuth()

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside className="flex w-56 shrink-0 flex-col bg-slate-900 text-slate-100">
        <div className="border-b border-slate-800 px-4 py-5">
          <h1 className="text-lg font-semibold tracking-tight">AnonShare</h1>
          {user && <p className="mt-1 truncate text-xs text-slate-400">{user.pseudonym}</p>}
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          <NavLink to="/feed" className={navClass}>
            Feed
          </NavLink>
          <NavLink to="/groups" className={navClass}>
            Groups
          </NavLink>
          {isAdmin && (
            <NavLink to="/admin" className={navClass}>
              Admin
            </NavLink>
          )}
        </nav>
        <div className="border-t border-slate-800 p-3">
          <button
            type="button"
            onClick={logout}
            className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto bg-white">
        <Outlet />
      </main>
    </div>
  )
}
