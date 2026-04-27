import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface NavItem {
  to: string
  label: string
  mobileLabel?: string
  icon: string
  roles: string[]
}

const NAV_ITEMS: NavItem[] = [
  { to: '/tenants',    label: 'Кинорумы',      icon: '🏢', roles: ['superadmin'] },
  { to: '/halls',      label: 'Залы',           icon: '🎬', roles: ['admin'] },
  { to: '/categories', label: 'Категории',      mobileLabel: 'Катег.', icon: '🗂️', roles: ['admin'] },
  { to: '/products',   label: 'Товары',         icon: '📦', roles: ['admin'] },
  { to: '/bookings',   label: 'Бронирования',   mobileLabel: 'Брони', icon: '🗓️', roles: ['admin', 'operator'] },
  { to: '/orders',     label: 'Заказы',         icon: '🧾', roles: ['admin', 'operator'] },
  { to: '/stock',      label: 'Склад',          icon: '📦', roles: ['admin', 'operator'] },
  { to: '/staff',      label: 'Сотрудники',     mobileLabel: 'Сотр.', icon: '👥', roles: ['admin'] },
]

export default function Layout() {
  const { auth, logout } = useAuth()
  const role = auth?.role ?? ''

  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(role))

  return (
    <div className="min-h-screen bg-gray-50 lg:flex lg:h-screen">
      <aside className="hidden w-60 bg-white border-r border-gray-200 lg:flex lg:flex-col">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🎬</span>
            <div>
              <p className="font-semibold text-gray-900 text-sm leading-tight">KinoRoom</p>
              <p className="text-xs text-gray-400 capitalize">{role}</p>
            </div>
          </div>
        </div>

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

      <header className="sticky top-0 z-20 border-b border-gray-200 bg-white px-4 py-3 lg:hidden">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-2xl">🎬</span>
            <div className="min-w-0">
              <p className="font-semibold text-gray-900 text-sm leading-tight">KinoRoom</p>
              <p className="text-xs text-gray-400 truncate">{auth?.username}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="shrink-0 text-sm text-gray-500 hover:text-red-500 transition-colors"
          >
            Выйти
          </button>
        </div>
      </header>

      <main className="pb-20 lg:flex-1 lg:overflow-y-auto lg:pb-0">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-30 grid border-t border-gray-200 bg-white shadow-lg lg:hidden"
        style={{ gridTemplateColumns: `repeat(${visibleItems.length}, minmax(0, 1fr))` }}>
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex min-h-[56px] flex-col items-center justify-center gap-0.5 px-1 text-[11px] font-medium transition-colors ${
                isActive ? 'text-brand-700 bg-brand-50' : 'text-gray-500'
              }`
            }
          >
            <span className="text-lg leading-none">{item.icon}</span>
            <span className="max-w-full truncate">{item.mobileLabel ?? item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
