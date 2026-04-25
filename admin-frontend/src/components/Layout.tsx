import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface NavItem {
  to: string
  label: string
  icon: string
  roles: string[]
}

const NAV_ITEMS: NavItem[] = [
  { to: '/tenants',    label: 'Кинорумы',      icon: '🏢', roles: ['superadmin'] },
  { to: '/halls',      label: 'Залы',           icon: '🎬', roles: ['admin'] },
  { to: '/categories', label: 'Категории',      icon: '🗂️', roles: ['admin'] },
  { to: '/products',   label: 'Товары',         icon: '📦', roles: ['admin'] },
  { to: '/bookings',   label: 'Бронирования',   icon: '🗓️', roles: ['admin', 'operator'] },
  { to: '/orders',     label: 'Заказы',         icon: '🧾', roles: ['admin', 'operator'] },
  { to: '/stock',      label: 'Склад',          icon: '📦', roles: ['admin', 'operator'] },
  { to: '/staff',      label: 'Сотрудники',     icon: '👥', roles: ['admin'] },
]

export default function Layout() {
  const { auth, logout } = useAuth()
  const role = auth?.role ?? ''

  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(role))

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🎬</span>
            <div>
              <p className="font-semibold text-gray-900 text-sm leading-tight">Kinorum</p>
              <p className="text-xs text-gray-400 capitalize">{role}</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="px-3 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between px-2">
            <div>
              <p className="text-sm font-medium text-gray-800 truncate max-w-[120px]">
                {auth?.username}
              </p>
              {auth?.tenant_id && (
                <p className="text-xs text-gray-400">tenant #{auth.tenant_id}</p>
              )}
            </div>
            <button
              onClick={logout}
              className="text-xs text-gray-400 hover:text-red-500 transition-colors"
              title="Выйти"
            >
              Выйти
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
